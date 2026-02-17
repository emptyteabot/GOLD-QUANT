"""
推特监控模块 - 华尔街顶级信息源
"""
import asyncio
import tweepy
from datetime import datetime, timedelta
from typing import Optional, Dict, Set
from openai import AsyncOpenAI
from config_ultimate import config
from wechat_notifier import notifier


class TwitterMonitor:
    """推特监控器 - 监控华尔街顶级账号"""
    
    def __init__(self):
        # 初始化 Twitter API 客户端
        self.client = None
        if config.TWITTER_BEARER_TOKEN:
            self.client = tweepy.Client(bearer_token=config.TWITTER_BEARER_TOKEN)
        
        # Grok AI 客户端 (xAI 的 Grok 最懂推特)
        self.ai_client = AsyncOpenAI(
            api_key=config.GROK_API_KEY,
            base_url=config.GROK_BASE_URL
        )
        
        # 已处理的推文ID
        self.seen_tweets: Set[str] = set()
        
        # 用户ID缓存 (username -> user_id)
        self.user_id_cache: Dict[str, str] = {}
        
        # 统计
        self.tweets_checked: int = 0
        self.tweets_analyzed: int = 0
        self.alert_count: int = 0
        
        # 上次警报时间
        self.last_alert_time: float = 0
        self.alert_cooldown: int = 300  # 5分钟冷却
    
    def _get_user_ids(self) -> Dict[str, str]:
        """获取监控账号的用户ID"""
        if not self.client:
            return {}
        
        if self.user_id_cache:
            return self.user_id_cache
        
        try:
            # 批量获取用户信息
            response = self.client.get_users(
                usernames=config.TWITTER_WATCHLIST,
                user_fields=["id", "username"]
            )
            
            if response.data:
                for user in response.data:
                    self.user_id_cache[user.username] = user.id
                
                print(f"✅ 成功获取 {len(self.user_id_cache)} 个推特账号ID")
            
            return self.user_id_cache
            
        except Exception as e:
            print(f"❌ 获取推特用户ID失败: {e}")
            return {}
    
    async def fetch_recent_tweets(self) -> list:
        """
        获取监控账号的最新推文
        
        Returns:
            [(tweet_id, username, text, created_at, url), ...]
        """
        if not self.client:
            print("⚠️ 未配置 Twitter API，跳过推特监控")
            return []
        
        user_ids = self._get_user_ids()
        if not user_ids:
            return []
        
        tweets = []
        
        try:
            # 获取每个用户的最新推文
            for username, user_id in user_ids.items():
                try:
                    response = self.client.get_users_tweets(
                        id=user_id,
                        max_results=5,  # 每个账号最新5条
                        tweet_fields=["created_at", "text"],
                        exclude=["retweets", "replies"]  # 排除转推和回复
                    )
                    
                    if response.data:
                        for tweet in response.data:
                            # 过滤关键词
                            if self._contains_keywords(tweet.text):
                                tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"
                                tweets.append((
                                    tweet.id,
                                    username,
                                    tweet.text,
                                    tweet.created_at,
                                    tweet_url
                                ))
                    
                    # 避免 API 限流
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️ 获取 @{username} 推文失败: {e}")
                    continue
            
            return tweets
            
        except Exception as e:
            print(f"❌ 推特抓取失败: {e}")
            return []
    
    def _contains_keywords(self, text: str) -> bool:
        """检查推文是否包含关键词"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in config.TWITTER_KEYWORDS)
    
    async def analyze_tweet_with_grok(self, tweet_text: str, username: str) -> Optional[Dict]:
        """
        使用 Grok 分析推文对黄金的影响
        
        Grok 的优势: 
        - 实时训练数据 (包含最新推特内容)
        - 理解推特文化和缩写
        - 更准确的情感分析
        """
        system_prompt = """你是华尔街顶级黄金交易员,专门分析推特上的市场信息。

你的任务是分析这条推文对黄金(XAU/USD)价格的**短期影响**(1小时内)。

评分标准:
- -10到-7: 极度利空 (如: 美联储意外鹰派、美元暴涨、地缘风险解除)
- -6到-4: 中度利空 (如: 强劲经济数据、风险偏好回升)
- -3到-1: 轻微利空
- 0: 中性
- +1到+3: 轻微利多
- +4到+6: 中度利多 (如: 通胀担忧、美元走弱)
- +7到+10: 极度利多 (如: 地缘冲突、银行危机、美联储鸽派)

is_urgent 判断:
- 涉及突发事件、重大数据、美联储决策时为 true
- 普通评论、技术分析为 false

注意推特特点:
- 关注 @DeItaone、@FirstSquawk 等快讯账号的时效性
- 识别推特缩写 (如: DXY=美元指数, FOMC=美联储会议)
- 警惕假消息和谣言

返回JSON格式:
{"score": 整数, "summary": "20字以内分析", "is_urgent": true/false}"""

        user_prompt = f"推特账号: @{username}\n推文内容: {tweet_text}"
        
        try:
            response = await self.ai_client.chat.completions.create(
                model=config.GROK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析 JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            import json
            result = json.loads(result_text)
            
            if "score" in result and "summary" in result and "is_urgent" in result:
                return result
            else:
                print(f"⚠️ Grok 返回格式不正确: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Grok API 调用失败: {e}")
            return None
    
    async def check_alert_conditions(
        self,
        username: str,
        tweet_text: str,
        tweet_url: str,
        analysis: Dict
    ) -> bool:
        """检查是否触发警报"""
        score = analysis.get('score', 0)
        is_urgent = analysis.get('is_urgent', False)
        
        # 判断条件: 分数低于阈值 或 标记为紧急
        should_alert = False
        
        if score <= config.THRESHOLD_SENTIMENT and is_urgent:
            should_alert = True
        elif abs(score) >= 8:  # 极端情况 (无论利多利空都推送)
            should_alert = True
        
        if should_alert:
            # 检查冷却时间
            current_time = datetime.now().timestamp()
            if current_time - self.last_alert_time < self.alert_cooldown:
                print(f"⏳ 警报冷却中,跳过推送")
                return False
            
            print(f"🚨 触发推特警报: @{username} (分数: {score})")
            
            # 发送警报
            success = await notifier.send_twitter_alert(
                username=username,
                tweet_text=tweet_text[:200],  # 限制长度
                sentiment_score=score,
                analysis=analysis.get('summary', ''),
                tweet_url=tweet_url
            )
            
            if success:
                self.last_alert_time = current_time
                self.alert_count += 1
                return True
        
        return False
    
    async def run(self):
        """主监控循环"""
        print(f"🐦 推特监控器启动")
        print(f"⏱️  检查间隔: {config.TWITTER_CHECK_INTERVAL}秒")
        print(f"👥 监控账号: {len(config.TWITTER_WATCHLIST)}个")
        print(f"🔑 关键词: {', '.join(config.TWITTER_KEYWORDS[:5])}...")
        print("-" * 60)
        
        if not self.client:
            print("❌ 未配置 Twitter API，推特监控已禁用")
            print("💡 提示: 访问 https://developer.twitter.com/ 申请 API")
            return
        
        # 预加载用户ID
        self._get_user_ids()
        
        while True:
            try:
                # 获取最新推文
                tweets = await self.fetch_recent_tweets()
                
                for tweet_id, username, text, created_at, url in tweets:
                    # 跳过已处理的推文
                    if tweet_id in self.seen_tweets:
                        continue
                    
                    self.seen_tweets.add(tweet_id)
                    self.tweets_checked += 1
                    
                    print(f"\n🐦 @{username}: {text[:60]}...")
                    
                    # 使用 Grok 分析
                    analysis = await self.analyze_tweet_with_grok(text, username)
                    
                    if analysis:
                        self.tweets_analyzed += 1
                        score = analysis.get('score', 0)
                        summary = analysis.get('summary', '')
                        is_urgent = analysis.get('is_urgent', False)
                        
                        # 输出分析结果
                        emoji = "🔴" if score < -5 else "🟡" if score < 0 else "🟢"
                        urgent_flag = "⚡紧急" if is_urgent else ""
                        print(f"   {emoji} 分数: {score:+d}/10 {urgent_flag}")
                        print(f"   💬 分析: {summary}")
                        
                        # 检查警报条件
                        await self.check_alert_conditions(username, text, url, analysis)
                    
                    # 避免 API 限流
                    await asyncio.sleep(2)
                
                # 定期输出统计
                if self.tweets_checked > 0 and self.tweets_checked % 20 == 0:
                    print(f"\n📊 推特统计: 检查 {self.tweets_checked} | 分析 {self.tweets_analyzed} | 警报 {self.alert_count}")
                
                # 等待下次检查
                await asyncio.sleep(config.TWITTER_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ 推特监控异常: {e}")
                await asyncio.sleep(30)


# 测试函数
async def test_twitter_monitor():
    """测试推特监控器"""
    monitor = TwitterMonitor()
    
    # 测试 Grok 分析
    test_cases = [
        ("DeItaone", "BREAKING: Fed's Powell says inflation remains stubborn, further rate hikes likely"),
        ("GoldTelegraph_", "GOLD ALERT: Geopolitical tensions escalate, safe-haven demand surges"),
        ("zerohedge", "US Dollar Index (DXY) spikes to 2-year high on strong jobs data")
    ]
    
    print("🧪 测试 Grok 推文分析:\n")
    for username, text in test_cases:
        print(f"@{username}: {text}")
        result = await monitor.analyze_tweet_with_grok(text, username)
        if result:
            print(f"结果: {result}\n")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_twitter_monitor())




