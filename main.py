"""
股票技术分析系统主程序

使用模块化架构重构的股票技术分析系统
"""

import os
import re
import pytz
import time
from datetime import datetime
from core import StockAnalyzer
from utils.logger import get_logger
from llm import LLMAnalyzer
from push_notification import PushNotifier
from config import Config
from strategy import select_stocks

# 设置日志
logger = get_logger(__name__)


def extract_sentiment_from_advice(advice: str) -> float:
    """根据AI投资建议文本简单情感分析，返回[-1,1]分数"""
    if not advice:
        return 0.0
    advice = advice.lower()
    if '买入' in advice or '积极' in advice or '看多' in advice:
        return 0.7
    elif '卖出' in advice or '谨慎' in advice or '看空' in advice:
        return -0.7
    elif '观望' in advice or '中性' in advice:
        return 0.0
    return 0.0


def main():
    """主程序入口"""
    start_time = time.time()
    print("🚀 启动股票技术分析系统...")
    logger.info("🚀 启动股票技术分析系统...")
    
    try:
        # 加载和验证配置
        print("⚙️ 加载配置文件...")
        config = Config()
        config.print_config_status()
        errors = config.validate_config()
        if errors:
            print("⚠️ 配置错误：")
            logger.error("⚠️ 配置错误：")
            for error in errors:
                print(f"  {error}")
                logger.error(f"  {error}")
            print("\n📝 请检查配置后重新运行")
            logger.error("\n📝 请检查配置后重新运行")
            return 1

        # 维护自选股票池
        stock_pool = {
            '北方稀土': 'sh600111',
            '中航沈飞': 'sh600760',
            '药明康德': 'sh603259',
            '美图公司': '01357.HK',
            '中国船舶': 'sh600150',
            '航发动力': 'sh600893',
            '国泰君安国际': '01788.HK',
        }

        logger.info("开始股票技术分析...")
        logger.info(f"分析股票: {list(stock_pool.keys())}")

        # 初始化分析器和相关组件
        analyzer = StockAnalyzer(stock_pool, config=config)
        llm = LLMAnalyzer(config.llm_api_key, config.llm_base_url, config.llm_model)
        notifier = PushNotifier()

        # 获取股票数据并计算技术指标
        print("📊 步骤1: 获取股票数据...")
        logger.info("步骤1: 获取股票数据")
        if not analyzer.fetch_data():
            print("❌ 数据获取失败，终止分析")
            logger.error("数据获取失败，终止分析")
            return 1
        print("✅ 数据获取完成")

        # 构建用于策略分析的数据
        print("📊 计算技术指标...")
        stock_data_dict = {}
        for name, code in stock_pool.items():
            if code not in analyzer.data:
                continue
            df_ind = analyzer.calculate_indicators(code)
            if df_ind is not None:
                stock_data_dict[code] = df_ind

        if not stock_data_dict:
            print("❌ 没有有效的股票数据进行策略分析")
            logger.error("没有有效的股票数据进行策略分析")
            return 1

        # 本地策略信号
        print("📊 步骤2: 运行本地选股策略...")
        logger.info("步骤2: 运行本地选股策略")
        results = select_stocks(stock_data_dict)
        print("✅ 策略分析完成")

        # 构造AI prompt
        print("📊 步骤3: 准备AI分析...")
        logger.info("步骤3: 准备AI分析")
        ai_input = []
        for code, res in results.items():
            name = [k for k, v in stock_pool.items() if v == code][0]
            ai_input.append({
                'name': name,
                'code': code,
                'signal': res['signal'],
                'score': res['score'],
                'reason': res['reason'],
            })

        # 获取当前市场环境信息
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        ai_prompt = _generate_ai_prompt(current_date, ai_input)

        # 调用AI分析
        print("📊 步骤4: 执行AI智能分析...")
        logger.info("步骤4: 执行AI智能分析")
        ai_result = llm.client.chat.completions.create(
            model=llm.model,
            messages=[
                {"role": "system", "content": _get_system_prompt()},
                {"role": "user", "content": ai_prompt}
            ],
            temperature=0.8,
            stream=False
        )
        ai_text = ai_result.choices[0].message.content
        print("✅ AI分析完成")

        # 解析AI输出，提取关键信息
        print("📊 解析AI分析结果...")
        analysis_summary = _parse_ai_analysis(ai_text, current_date)

        # 生成推送内容
        push_text = _generate_push_content(analysis_summary)

        # 推送通知（在合适的时间）
        _handle_push_notification(notifier, push_text)

        # 生成详细HTML报告
        print("📊 步骤5: 生成HTML报告...")
        logger.info("步骤5: 生成HTML报告")
        analyzer.pool_ai_analysis = ai_text  # 传递整体AI分析结果
        report_path = analyzer.run_analysis()
        
        if report_path:
            end_time = time.time()
            runtime = end_time - start_time
            print("🎉" + "="*60)
            print(f"✅ 分析完成！报告已保存到: {report_path}")
            print(f"🌐 在浏览器中查看: file://{os.path.abspath(report_path)}")
            print(f"⏱️  总运行时间: {runtime:.2f} 秒")
            print("="*60)
            logger.info(f"✅ 分析完成！报告已保存到: {report_path}")
            return 0
        else:
            end_time = time.time()
            runtime = end_time - start_time
            print(f"❌ 分析失败，请检查错误信息 (运行时间: {runtime:.2f} 秒)")
            logger.error("❌ 分析失败，请检查错误信息")
            return 1

    except Exception as e:
        end_time = time.time()
        runtime = end_time - start_time
        print(f"❌ 程序执行出错: {str(e)} (运行时间: {runtime:.2f} 秒)")
        logger.error(f"程序执行出错: {str(e)}")
        return 1


def _generate_ai_prompt(current_date: str, ai_input: list) -> str:
    """生成AI分析提示词"""
    return (
        f"你是一位专业的量化投资顾问，专注于基于技术指标数据的股票分析。\n"
        f"当前日期：{current_date}\n\n"
        f"以下是我的自选股票池的近期技术信号与打分（基于实际技术指标计算）：\n"
        + "\n".join([f"{d['name']}({d['code']}): {d['signal']} | score: {d['score']:.2f} | {d['reason']}" for d in ai_input])
        + f"\n\n请基于这些实际的技术信号数据，对股票池进行专业分析，并按以下结构输出：\n\n"
        "【1. 技术面整体分析】\n"
        "- 基于技术信号判断当前市场技术环境\n"
        "- 分析股票池整体技术强度分布\n"
        "- 识别技术面强势和弱势股票\n"
        "- 评估技术指标的一致性和背离情况\n\n"
        "【2. 行业技术特征分析】\n"
        "- 分析股票池中各行业的技术表现\n"
        "- 识别技术面领先和落后的行业\n"
        "- 评估行业间的技术轮动特征\n"
        "- 分析行业技术趋势的持续性\n\n"
        "【3. 个股技术深度分析】\n"
        "- 必须对股票池中的每只股票进行详细技术面评价，格式如下：\n"
        "  *股票名(代码)：\n"
        "  - 信号强度：具体数值及评级\n"
        "  - 指标组合：主要技术指标分析\n"
        "  - 形态识别：技术形态判断\n"
        "  - 风险点：技术面风险提示\n"
        "  - 机会点：技术面机会提示\n\n"
        "【4. 投资策略建议】\n"
        "- 推荐排序（Top5只）：\n"
        "  格式：股票名(代码) | 操作建议 | 技术信号 | 技术逻辑 | 风险等级 | 技术目标位\n"
        "- 仓位管理建议：\n"
        "  * 基于技术强度分配仓位\n"
        "  * 单只股票仓位上限\n"
        "  * 技术面建仓时机\n"
        "- 风险控制措施：\n"
        "  * 技术止损位设置\n"
        "  * 技术止盈策略\n"
        "  * 技术面风险分散\n\n"
        "【5. 技术面机会与风险】\n"
        "- 技术面机会：\n"
        "  * 技术突破机会\n"
        "  * 技术修复机会\n"
        "  * 技术轮动机会\n"
        "- 技术面风险：\n"
        "  * 技术背离风险\n"
        "  * 技术超买超卖风险\n"
        "  * 技术支撑压力风险\n"
        "- 技术面应对策略\n\n"
        "【6. 技术情绪评分】\n"
        "- 综合技术情绪评分：[-1.0 极度悲观 至 1.0 极度乐观]\n"
        "- 评分依据：技术指标综合判断\n"
        "- 技术情绪变化趋势\n\n"
        "【7. 技术操作时间窗口】\n"
        "- 短期技术操作（1-3天）\n"
        "- 中期技术布局（1-2周）\n"
        "- 长期技术持有（1-3个月）\n\n"
        "重要提醒：\n"
        "- 仅基于提供的技术信号数据进行分析\n"
        "- 不要编造或推测市场环境、资金流向等未提供的信息\n"
        "- 专注于技术指标的逻辑分析和策略制定\n"
        "- 给出基于技术面的可操作建议\n"
        "- 注重技术面风险控制"
    )


def _get_system_prompt() -> str:
    """获取系统提示词"""
    return """你是一位专业的量化投资顾问，专注于技术指标分析，具备以下专业能力：
1. 技术指标分析：MACD、KDJ、RSI、布林带、DMI、VR、ROC等指标的专业解读
2. 技术形态识别：支撑阻力、趋势线、形态分析、量价关系
3. 技术风险管理：技术止损、技术止盈、技术面风险控制
4. 技术策略制定：基于技术信号的交易策略、仓位管理
5. 实战经验：丰富的技术分析经验，熟悉各类技术指标的应用

请仅基于提供的技术信号数据进行客观、理性的技术分析。不要编造或推测未提供的信息，专注于技术指标的逻辑分析和策略制定。"""


def _parse_ai_analysis(ai_text: str, current_date: str) -> dict:
    """解析AI分析结果"""
    try:
        analysis_summary = {
            'date': current_date,
            'market_analysis': '',
            'overall_advice': '',
            'emotion_score': None,
            'top_recommendations': []
        }
        
        # 提取技术面整体分析
        market_match = re.search(r'【1\. 技术面整体分析】([\s\S]+?)【2\.', ai_text)
        if market_match:
            analysis_summary['market_analysis'] = market_match.group(1).strip()
        
        # 提取投资策略建议
        strategy_match = re.search(r'【4\. 投资策略建议】([\s\S]+?)【5\.', ai_text)
        if strategy_match:
            analysis_summary['overall_advice'] = strategy_match.group(1).strip()
        
        # 提取情绪评分
        emotion_match = re.search(r'综合[技术]*情绪评分[：:]\s*([-+]?\d*\.?\d+)', ai_text)
        if emotion_match:
            try:
                analysis_summary['emotion_score'] = float(emotion_match.group(1))
            except ValueError:
                pass
        
        # 提取推荐排序
        recommendation_section = analysis_summary['overall_advice']
        if recommendation_section:
            ranking_match = re.search(r'推荐排序[：:]*([\s\S]+?)(?:仓位管理|$)', recommendation_section)
            if ranking_match:
                ranking_text = ranking_match.group(1)
                stock_matches = re.findall(r'(\d+)[\.\)]\s*([^(|]+?)\(([^)]+?)\)', ranking_text)
                for rank, stock_name, stock_code in stock_matches[:5]:
                    analysis_summary['top_recommendations'].append({
                        'rank': int(rank),
                        'name': stock_name.strip(),
                        'code': stock_code.strip()
                    })
        
        return analysis_summary
        
    except Exception as e:
        logger.error(f"解析AI分析结果失败: {str(e)}")
        return {'date': current_date, 'error': str(e)}


def _generate_push_content(analysis_summary: dict) -> str:
    """生成推送内容"""
    try:
        push_lines = [f"📊 {analysis_summary['date']} AI股票池策略分析"]
        
        if analysis_summary.get('market_analysis'):
            push_lines.append(f"\n📊 技术面分析: {analysis_summary['market_analysis'][:100]}...")
        
        if analysis_summary.get('top_recommendations'):
            push_lines.append(f"\n🎯 推荐Top5:")
            for rec in analysis_summary['top_recommendations']:
                push_lines.append(f"  {rec['rank']}. {rec['name']}({rec['code']})")
        
        if analysis_summary.get('emotion_score') is not None:
            score = analysis_summary['emotion_score']
            emotion_icon = "😊" if score > 0.3 else "😐" if score > -0.3 else "😟"
            push_lines.append(f"\n{emotion_icon} 市场情绪: {score:.2f}")
        
        if analysis_summary.get('overall_advice'):
            push_lines.append(f"\n💡 策略要点: {analysis_summary['overall_advice'][:200]}...")
        
        return '\n'.join(push_lines)
        
    except Exception as e:
        logger.error(f"生成推送内容失败: {str(e)}")
        return f"📊 {analysis_summary.get('date', 'Unknown')} 技术分析报告生成完成"


def _handle_push_notification(notifier: PushNotifier, push_text: str):
    """处理推送通知"""
    try:
        # 9:00中国时间推送
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        if now.hour == 9:
            logger.info("发送推送通知...")
            notifier.push_to_serverchan('今日AI技术分析策略', push_text)
        else:
            logger.info("非推送时间，跳过推送通知")
    except Exception as e:
        logger.error(f"推送通知处理失败: {str(e)}")


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 