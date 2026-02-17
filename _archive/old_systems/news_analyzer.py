"""
修复 news_analyzer.py - 使用 Grok API
"""
import asyncio
import feedparser
import json
from datetime import datetime
from typing import Optional, Dict, Set
from openai import AsyncOpenAI
from config_ultimate import config
from notifier import notifier


class NewsAnalyzer:
    """新闻分析器 - 使用 Grok AI"""
    
    def __init__(self):
        # 根据配置选择 AI 客户端
        if config.AI_PROVIDER == "grok":
            self.client = AsyncOpenAI(
                api_key=config.GROK_API_KEY,
                base_url=config.GROK_BASE_URL
            )
            self.model = config.GROK_MODEL
        else:
            self.client = AsyncOpenAI(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL
            )
            self.model = "deepseek-chat"
        
        # 已处理的新闻链接
        self.seen_links: Set[str] = set()
        
        # 上次警报时间
        self.last_alert_time: float = 0
        self.alert_cooldown: int = 600  # 10分钟冷却
        
        # 统计数据
        self.news_checked: int = 0
        self.news_analyzed: int = 0
        self.alert_count: int = 0
    
    async def analyze_sentiment(self, news_text: str) -> Optional[Dict]:
        """
        使用 AI 分析新闻情感
        
        Args:
            news_text: 新闻标题或内容
        
        Returns:
            {
                "score": int (-10到10),
                "summary": str (简短分析),
                "is_urgent": bool (是否紧急)
            }
        """
        system_prompt = """你是一位华尔街顶级黄金交易员,拥有20年市场经验。

你的任务是分析新闻对黄金(XAU/USD)价格的**短期影响**(1小时内)。

评分标准:
- -10: 极度利空,可能导致黄金暴跌 (如: 美联储意外加息、美元暴涨、地缘风险解除)
- -7到-9: 重大利空 (如: 强劲非农数据、鹰派美联储讲话)
- -4到-6: 中度利空 (如: 美债收益率上升、风险偏好回升)
- -1到-3: 轻微利空
- 0: 中性,对黄金无明显影响
- +1到+3: 轻微利多
- +4到+6: 中度利多 (如: 通胀数据超预期、美元走弱)
- +7到+9: 重大利多 (如: 地缘冲突升级、银行危机)
- +10: 极度利多,可能导致黄金暴涨 (如: 美联储紧急降息、重大战争)

is_urgent 判断标准:
- 涉及美联储决议、非农数据、CPI数据、地缘冲突等重大事件时为 true
- 普通市场评论、技术分析、历史回顾等为 false

请以JSON格式返回,不要有任何其他文字:
{"score": 整数, "summary": "20字以内的简短分析", "is_urgent": true/false}"""

        user_prompt = f"分析这条新闻对黄金的影响:\n\n{news_text}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 尝试解析 JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            
            if "score" in result and "summary" in result and "is_urgent" in result:
                return result
            else:
                print(f"⚠️ AI 返回格式不正确: {result}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"原始返回: {result_text}")
            return None
        except Exception as e:
            print(f"❌ AI API 调用失败: {e}")
            return None
    
    async def fetch_news_from_feed(self, feed_url: str) -> list:
        """
        从 RSS 源获取新闻
        
        Returns:
            [(title, link, published), ...]
        """
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
            
            news_list = []
            for entry in feed.entries[:5]:
                title = entry.get('title', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # 过滤: 标题必须包含黄金相关关键词
                keywords = ['gold', 'xau', 'bullion', '黄金', 'precious metal']
                if any(kw in title.lower() for kw in keywords):
                    news_list.append((title, link, published))
            
            return news_list
            
        except Exception as e:
            print(f"❌ RSS 抓取失败 ({feed_url}): {e}")
            return []
    
    async def check_alert_conditions(
        self, 
        news_title: str, 
        news_link: str,
        analysis: Dict
    ) -> bool:
        """检查是否触发警报"""
        score = analysis.get('score', 0)
        is_urgent = analysis.get('is_urgent', False)
        
        if score <= config.THRESHOLD_SENTIMENT and is_urgent:
            current_time = datetime.now().timestamp()
            if current_time - self.last_alert_time < self.alert_cooldown:
                print(f"⏳ 警报冷却中,跳过推送")
                return False
            
            print(f"🚨 触发舆情警报: {news_title} (分数: {score})")
            
            success = await notifier.send_news_alert(
                news_title=news_title,
                sentiment_score=score,
                analysis=analysis.get('summary', ''),
                news_url=news_link
            )
            
            if success:
                self.last_alert_time = current_time
                self.alert_count += 1
                return True
        
        return False
    
    async def run(self):
        """主监控循环"""
        print(f"📰 舆情分析器启动")
        print(f"🧠 AI 引擎: {config.AI_PROVIDER.upper()}")
        print(f"⏱️  检查间隔: {config.NEWS_CHECK_INTERVAL}秒")
        print(f"📊 情感阈值: {config.THRESHOLD_SENTIMENT}/10")
        print(f"🔗 新闻源数量: {len(config.NEWS_FEEDS)}")
        print("-" * 60)
        
        while True:
            try:
                for feed_url in config.NEWS_FEEDS:
                    news_list = await self.fetch_news_from_feed(feed_url)
                    
                    for title, link, published in news_list:
                        if link in self.seen_links:
                            continue
                        
                        self.seen_links.add(link)
                        self.news_checked += 1
                        
                        print(f"\n📰 发现新闻: {title[:50]}...")
                        
                        analysis = await self.analyze_sentiment(title)
                        
                        if analysis:
                            self.news_analyzed += 1
                            score = analysis.get('score', 0)
                            summary = analysis.get('summary', '')
                            is_urgent = analysis.get('is_urgent', False)
                            
                            emoji = "🔴" if score < -5 else "🟡" if score < 0 else "🟢"
                            urgent_flag = "⚡紧急" if is_urgent else ""
                            print(f"   {emoji} 分数: {score:+d}/10 {urgent_flag}")
                            print(f"   💬 分析: {summary}")
                            
                            await self.check_alert_conditions(title, link, analysis)
                        
                        await asyncio.sleep(2)
                
                if self.news_checked > 0 and self.news_checked % 10 == 0:
                    print(f"\n📊 统计: 检查 {self.news_checked} | 分析 {self.news_analyzed} | 警报 {self.alert_count}")
                
                await asyncio.sleep(config.NEWS_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ 舆情监控异常: {e}")
                await asyncio.sleep(30)


# 测试函数
async def test_news_analyzer():
    """测试新闻分析器"""
    analyzer = NewsAnalyzer()
    
    test_cases = [
        "美联储主席鲍威尔: 通胀仍然顽固,可能需要进一步加息",
        "地缘冲突升级,避险情绪推动黄金大涨",
        "美国非农就业数据远超预期,美元指数飙升"
    ]
    
    print(f"🧪 测试 {config.AI_PROVIDER.upper()} 情感分析:\n")
    for text in test_cases:
        print(f"新闻: {text}")
        result = await analyzer.analyze_sentiment(text)
        if result:
            print(f"结果: {result}\n")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_news_analyzer())
