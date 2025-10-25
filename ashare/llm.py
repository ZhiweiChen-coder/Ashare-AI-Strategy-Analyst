import json
import os
from typing import Dict, Any, Optional

import openai
import pandas as pd
from openai import OpenAI
import re


def format_analysis_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化分析结果，确保输出格式统一

    Args:
        result (Dict[str, Any]): 原始分析结果

    Returns:
        Dict[str, Any]: 格式化后的结果
    """
    if not result:
        return {
            "AI分析结果": {
                "分析状态": "分析失败",
                "失败原因": "无法获取API响应",
                "技术分析": "数据获取失败，无法提供分析。",
                "走势分析": "数据获取失败，无法提供分析。",
                "投资建议": "由于数据获取失败，暂不提供投资建议。",
                "风险提示": "数据不完整，投资决策需谨慎。"
            }
        }

    return result


def _create_system_prompt() -> str:
    """
    创建系统提示词

    Returns:
        str: 系统提示词
    """
    return """你是一个专业的金融分析师，将收到完整的股票历史数据和技术指标数据进行分析。
数据包括：
1. 历史数据：每日的开盘价、收盘价、最高价、最低价和成交量
2. 技术指标：所有交易日的各项技术指标数据
3. 市场趋势：当前的关键趋势数据

请基于这些完整的历史数据进行深入分析，包括以下方面：

1. 技术面分析
- 通过历史数据分析长期趋势
- 识别关键的支撑位和压力位
- 分析重要的技术形态
- 对所有技术指标进行综合研判
- 寻找指标之间的背离现象

2. 走势研判
- 判断当前趋势的强度和可能持续性
- 识别可能的趋势转折点
- 分析成交量和价格的配合情况
- 预判可能的运行区间

3. 投资建议
- 基于完整数据给出明确的操作建议
- 设置合理的止损和目标价位
- 建议适当的持仓时间和仓位控制
- 针对不同投资周期给出建议

4. 风险提示
- 通过历史数据识别潜在风险
- 列出需要警惕的技术信号
- 提供风险规避的具体建议
- 说明需要持续关注的指标

请注意：
- 结合全部历史数据做出判断
- 分析结果要有数据支持
- 避免过度简化或主观判断
- 必要时引用具体的历史数据点
- 结合多个维度的指标进行交叉验证

按照以下固定格式输出分析结果,不要包含任何markdown标记：

技术分析
1. 长期趋势分析：
趋势判断
突破情况
形态分析

2. 支撑和压力：
关键支撑位
关键压力位
突破可能性

3. 技术指标研判：
MACD指标
KDJ指标
RSI指标
布林带分析
其他关键指标

走势分析
1. 当前趋势：
趋势方向
趋势强度
持续性分析

2. 价量配合：
成交量变化
量价关系
市场活跃度

3. 关键位置：
当前位置
突破机会
调整空间

投资建议
1. 操作策略：
总体建议
买卖时机
仓位控制

2. 具体参数：
止损位设置
目标价位
持仓周期

3. 分类建议：
激进投资者建议
稳健投资者建议
保守投资者建议

风险提示
1. 风险因素：
技术面风险
趋势风险
位置风险

2. 防范措施：
止损设置
仓位控制
注意事项

3. 持续关注：
重点指标
关键价位
市场变化

最后给出总体总结。

请在最后单独输出一行：
情感分数: <分数>  # 取值范围[-1,1]，1为极度看多，-1为极度看空，0为中性
"""


def _format_data_for_prompt(df: pd.DataFrame, technical_indicators: pd.DataFrame) -> str:
    """
    将数据格式化为提示词，对早期数据进行采样处理

    Args:
        df (pd.DataFrame): 原始股票数据
        technical_indicators (pd.DataFrame): 技术指标数据

    Returns:
        str: 格式化后的数据字符串
    """
    # 复制数据框以避免修改原始数据
    df_dict = df.copy()
    technical_indicators_dict = technical_indicators.copy()

    # 将时间索引转换为字符串格式
    df_dict.index = df_dict.index.strftime('%Y-%m-%d')
    technical_indicators_dict.index = technical_indicators_dict.index.strftime('%Y-%m-%d')

    # 分割数据：最近60天的数据和之前的数据
    recent_dates = list(df_dict.index)[-60:]
    early_dates = list(df_dict.index)[:-60]

    # 对早期数据进行采样（每2天取一个点）
    sampled_early_dates = early_dates[::2]

    # 合并采样后的日期和最近日期
    selected_dates = sampled_early_dates + recent_dates

    # 构建完整的数据字典，只包含选定的日期
    data_dict = {
        "历史数据": {
            date: {
                "开盘价": f"{df_dict.loc[date, 'open']:.2f}",
                "收盘价": f"{df_dict.loc[date, 'close']:.2f}",
                "最高价": f"{df_dict.loc[date, 'high']:.2f}",
                "最低价": f"{df_dict.loc[date, 'low']:.2f}",
                "成交量": f"{int(df_dict.loc[date, 'volume']):,}"
            } for date in selected_dates
        },
        "技术指标": {
            date: {
                "趋势指标": {
                    "MACD": f"{technical_indicators_dict.loc[date, 'MACD']:.2f}",
                    "DIF": f"{technical_indicators_dict.loc[date, 'DIF']:.2f}",
                    "DEA": f"{technical_indicators_dict.loc[date, 'DEA']:.2f}",
                    "MA5": f"{technical_indicators_dict.loc[date, 'MA5']:.2f}",
                    "MA10": f"{technical_indicators_dict.loc[date, 'MA10']:.2f}",
                    "MA20": f"{technical_indicators_dict.loc[date, 'MA20']:.2f}",
                    "MA60": f"{technical_indicators_dict.loc[date, 'MA60']:.2f}",
                    "TRIX": f"{technical_indicators_dict.loc[date, 'TRIX']:.2f}",
                    "TRMA": f"{technical_indicators_dict.loc[date, 'TRMA']:.2f}"
                },
                "摆动指标": {
                    "KDJ-K": f"{technical_indicators_dict.loc[date, 'K']:.2f}",
                    "KDJ-D": f"{technical_indicators_dict.loc[date, 'D']:.2f}",
                    "KDJ-J": f"{technical_indicators_dict.loc[date, 'J']:.2f}",
                    "RSI": f"{technical_indicators_dict.loc[date, 'RSI']:.2f}",
                    "CCI": f"{technical_indicators_dict.loc[date, 'CCI']:.2f}",
                    "BIAS1": f"{technical_indicators_dict.loc[date, 'BIAS1']:.2f}",
                    "BIAS2": f"{technical_indicators_dict.loc[date, 'BIAS2']:.2f}",
                    "BIAS3": f"{technical_indicators_dict.loc[date, 'BIAS3']:.2f}"
                },
                "布林带": {
                    "上轨": f"{technical_indicators_dict.loc[date, 'BOLL_UP']:.2f}",
                    "中轨": f"{technical_indicators_dict.loc[date, 'BOLL_MID']:.2f}",
                    "下轨": f"{technical_indicators_dict.loc[date, 'BOLL_LOW']:.2f}"
                },
                "动向指标": {
                    "PDI": f"{technical_indicators_dict.loc[date, 'PDI']:.2f}",
                    "MDI": f"{technical_indicators_dict.loc[date, 'MDI']:.2f}",
                    "ADX": f"{technical_indicators_dict.loc[date, 'ADX']:.2f}",
                    "ADXR": f"{technical_indicators_dict.loc[date, 'ADXR']:.2f}"
                },
                "成交量指标": {
                    "VR": f"{technical_indicators_dict.loc[date, 'VR']:.2f}",
                    "AR": f"{technical_indicators_dict.loc[date, 'AR']:.2f}",
                    "BR": f"{technical_indicators_dict.loc[date, 'BR']:.2f}",
                },
                "动量指标": {
                    "ROC": f"{technical_indicators_dict.loc[date, 'ROC']:.2f}",
                    "MAROC": f"{technical_indicators_dict.loc[date, 'MAROC']:.2f}",
                    "MTM": f"{technical_indicators_dict.loc[date, 'MTM']:.2f}",
                    "MTMMA": f"{technical_indicators_dict.loc[date, 'MTMMA']:.2f}",
                    "DPO": f"{technical_indicators_dict.loc[date, 'DPO']:.2f}",
                    "MADPO": f"{technical_indicators_dict.loc[date, 'MADPO']:.2f}"
                },
                "其他指标": {
                    "EMV": f"{technical_indicators_dict.loc[date, 'EMV']:.2f}",
                    "MAEMV": f"{technical_indicators_dict.loc[date, 'MAEMV']:.2f}",
                    "DIF_DMA": f"{technical_indicators_dict.loc[date, 'DIF_DMA']:.2f}",
                    "DIFMA_DMA": f"{technical_indicators_dict.loc[date, 'DIFMA_DMA']:.2f}"
                }
            } for date in selected_dates
        }
    }

    # 计算关键变化率
    latest_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    last_week_close = df['close'].iloc[-6] if len(df) > 5 else prev_close
    last_month_close = df['close'].iloc[-21] if len(df) > 20 else prev_close

    data_dict["市场趋势"] = {
        "日涨跌幅": f"{((latest_close - prev_close) / prev_close * 100):.2f}%",
        "周涨跌幅": f"{((latest_close - last_week_close) / last_week_close * 100):.2f}%",
        "月涨跌幅": f"{((latest_close - last_month_close) / last_month_close * 100):.2f}%",
        "最新收盘价": f"{latest_close:.2f}",
        "最高价": f"{df['high'].max():.2f}",
        "最低价": f"{df['low'].min():.2f}",
        "平均成交量": f"{int(df['volume'].mean()):,}"
    }

    return json.dumps(data_dict, ensure_ascii=False, indent=2)


def _parse_analysis_response(analysis_text: str) -> Dict[str, Any]:
    """解析API返回的文本分析结果为结构化数据"""

    def clean_markdown(text: str) -> str:
        """清理格式并处理换行"""
        lines = text.split('\n')
        cleaned_lines = []

        for _line in lines:
            _line = _line.strip()
            if not _line:
                continue

            # 识别大标题
            if _line in ['技术分析', '走势分析', '投资建议', '风险提示', '总结', '总体总结']:
                continue

            # 处理数字标题
            if _line.startswith(('1.', '2.', '3.')):
                if cleaned_lines:
                    cleaned_lines.append('')  # 添加空行
                cleaned_lines.append(f'<p class="section-title">{_line}</p>')
                continue

            # 处理正文内容
            if ':' in _line:
                title, content = _line.split(':', 1)
                if content.strip():
                    cleaned_lines.append(f'<p class="item-title">{title}:</p>')
                    cleaned_lines.append(f'<p class="item-content">{content.strip()}</p>')
            else:
                cleaned_lines.append(f'<p>{_line}</p>')

        return '\n'.join(cleaned_lines)

    sections = {
        "技术分析": "",
        "走势分析": "",
        "投资建议": "",
        "风险提示": "",
        "总结": ""
    }

    current_section = None
    buffer = []

    # 按行处理文本
    for line in analysis_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        # 处理总结部分
        if line.startswith('总体总结'):
            if current_section:
                sections[current_section] = clean_markdown('\n'.join(buffer))
            current_section = "总结"
            buffer = [line.split('：', 1)[1] if '：' in line else line]
            continue

        # 处理主要部分
        if line in sections:
            if current_section and buffer:
                sections[current_section] = clean_markdown('\n'.join(buffer))
            current_section = line
            buffer = []
            continue

        if current_section:
            buffer.append(line)

    # 处理最后一个部分
    if current_section and buffer:
        sections[current_section] = clean_markdown('\n'.join(buffer))

    # 提取情感分数
    score_match = re.search(r'情感分数[:：]\s*([-+]?\d*\.?\d+)', analysis_text)
    if score_match:
        try:
            score = float(score_match.group(1))
            sections['情感分数'] = score
        except Exception:
            pass

    return {
        "AI分析结果": sections
    }


class APIBusyError(Exception):
    """API服务器繁忙时抛出的异常"""
    pass


class LLMAnalyzer:
    """使用 OpenAI SDK 与 llm API 交互的类"""

    def __init__(self, api_key: str, base_url: str, model: str = None):
        """
        初始化 llm 分析器

        Args:
            api_key (str): llm API 密钥
            base_url (str): llm API 基础 URL
            model (str): 使用的模型名称，默认为None则使用环境变量或空字符串
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model or os.environ.get('LLM_MODEL', '')

    def request_analysis(self, df: pd.DataFrame, technical_indicators: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        向 llm API 发送分析请求

        Args:
            df (pd.DataFrame): 原始股票数据
            technical_indicators (pd.DataFrame): 技术指标数据

        Returns:
            Optional[Dict[str, Any]]: API 响应的分析结果
        """
        try:
            # 准备数据
            print("开始准备数据...")
            data_str = _format_data_for_prompt(df, technical_indicators)
            print(f"数据准备完成，数据长度: {len(data_str)}")

            # 构建消息
            print("构建API请求消息...")
            messages = [
                {"role": "system", "content": _create_system_prompt()},
                {"role": "user", "content": f"请分析以下股票数据并给出专业的分析意见：\n{data_str}"}
            ]
            print(f"消息构建完成，系统提示词长度: {len(messages[0]['content'])}")
            print(f"用户消息长度: {len(messages[1]['content'])}")

            # 发送请求
            print("开始发送API请求...")
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=1.0,
                    stream=False
                )
                print("API请求发送成功")
            except Exception as api_e:
                # 检查是否是空响应导致的JSON解析错误
                if str(api_e).startswith("Expecting value: line 1 column 1 (char 0)"):
                    print("API返回空响应，服务器可能繁忙")
                    raise APIBusyError("API服务器繁忙，返回空响应") from api_e
                print(f"API请求发送失败: {str(api_e)}")
                raise  # 重新抛出其他类型的异常

            # 记录原始响应以便调试
            print("API 原始响应类型:", type(response))
            print("API 原始响应内容:", response)

            # 检查响应内容
            if not response:
                print("API返回空响应")
                return format_analysis_result({})

            if not hasattr(response, 'choices'):
                print(f"API响应缺少choices属性，响应结构: {dir(response)}")
                return format_analysis_result({})

            if not response.choices:
                print("API响应的choices为空")
                return format_analysis_result({})

            # 解析响应
            try:
                analysis_text = response.choices[0].message.content
                print("成功获取分析文本内容")
                print("分析文本:", analysis_text)
            except Exception as text_e:
                print(f"获取分析文本失败: {str(text_e)}")
                raise

            # 将文本响应组织成结构化数据
            print("开始解析分析文本...")
            result = _parse_analysis_response(analysis_text)
            print("分析文本解析完成")
            return result

        except APIBusyError as be:  # 处理API繁忙异常
            print(f"=== API繁忙错误 ===")
            print(f"错误详情: {str(be)}")
            print(f"错误类型: {type(be)}")
            return format_analysis_result({})
        except json.JSONDecodeError as je:
            print(f"=== JSON解析错误 ===")
            print(f"错误详情: {str(je)}")
            print(f"错误类型: {type(je)}")
            print(f"错误位置: {je.pos}")
            print(f"错误行列: 行 {je.lineno}, 列 {je.colno}")
            print(f"错误的文档片段: {je.doc[:100] if je.doc else 'None'}")
            return format_analysis_result({})
        except openai.APITimeoutError as te:
            print(f"=== API超时错误 ===")
            print(f"错误详情: {str(te)}")
            print(f"错误类型: {type(te)}")
            return format_analysis_result({})
        except openai.APIConnectionError as ce:
            print(f"=== API连接错误 ===")
            print(f"错误详情: {str(ce)}")
            print(f"错误类型: {type(ce)}")
            return format_analysis_result({})
        except openai.APIError as ae:
            print(f"=== API错误 ===")
            print(f"错误详情: {str(ae)}")
            print(f"错误类型: {type(ae)}")
            return format_analysis_result({})
        except openai.RateLimitError as re:
            print(f"=== API频率限制错误 ===")
            print(f"错误详情: {str(re)}")
            print(f"错误类型: {type(re)}")
            return format_analysis_result({})
        except Exception as e:
            print(f"=== 未预期的错误 ===")
            print(f"错误详情: {str(e)}")
            print(f"错误类型: {type(e)}")
            print(f"错误追踪:")
            import traceback
            traceback.print_exc()
            return format_analysis_result({})
    
    def generate_pool_analysis(self, pool_summary: list) -> Optional[str]:
        """
        生成股票池综合分析
        
        Args:
            pool_summary: 股票池汇总信息列表
            
        Returns:
            AI分析文本，失败时返回None
        """
        try:
            print("开始生成股票池AI分析...")
            
            # 构建股票池分析的提示词
            pool_info = "股票池综合分析：\n\n"
            for stock in pool_summary:
                pool_info += f"股票名称: {stock['name']}\n"
                pool_info += f"股票代码: {stock['code']}\n"
                pool_info += f"最新价格: {stock['price']:.2f}\n"
                pool_info += f"涨跌幅: {stock['change_pct']:.2f}%\n"
                pool_info += f"成交量: {stock['volume']}\n"
                pool_info += f"RSI: {stock['rsi']:.2f}\n"
                pool_info += f"MACD: {stock['macd']:.2f}\n"
                pool_info += "-" * 40 + "\n"
            
            system_prompt = """你是一个专业的股票投资分析师。请基于提供的股票池信息，进行综合分析并提供投资建议。

请按以下结构回答：

1. **市场整体分析**
   - 分析当前股票池的整体表现
   - 识别市场趋势和行业特点

2. **个股亮点分析** 
   - 挑选表现最好的2-3只股票
   - 分析其技术指标和投资价值

3. **风险提示**
   - 识别潜在风险点
   - 提供风险控制建议

4. **投资建议**
   - 给出具体的买卖建议
   - 建议仓位配置比例

请用中文回答，语言专业且易懂。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pool_info}
            ]
            
            print("发送股票池分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print("股票池AI分析生成成功")
                return analysis_text
            else:
                print("股票池AI分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成股票池AI分析失败: {str(e)}")
            return None

    def generate_fundamental_analysis(self, fundamental_data: list, analysis_params: Dict[str, Any]) -> Optional[str]:
        """
        生成基本面分析
        
        Args:
            fundamental_data: 基本面数据列表
            analysis_params: 分析参数
            
        Returns:
            基本面分析文本，失败时返回None
        """
        try:
            print(f"开始生成基本面分析: {analysis_params['type']}")
            
            # 构建基本面分析的数据信息
            fundamental_info = f"基本面分析 - {analysis_params['type']}：\n\n"
            fundamental_info += f"分析周期: {analysis_params['time_period']}\n"
            fundamental_info += f"分析日期: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n"
            
            for stock in fundamental_data:
                fundamental_info += f"股票名称: {stock['name']}\n"
                fundamental_info += f"股票代码: {stock['code']}\n"
                fundamental_info += f"当前价格: {stock['current_price']:.2f}\n"
                fundamental_info += f"52周最高: {stock['high_52w']:.2f}\n"
                fundamental_info += f"52周最低: {stock['low_52w']:.2f}\n"
                fundamental_info += f"价格波动率: {stock['price_volatility']:.2f}%\n"
                fundamental_info += f"平均成交量: {stock['avg_volume']:,.0f}\n"
                fundamental_info += f"价格趋势强度: {stock['price_trend']:.2f}\n"
                fundamental_info += f"成交量趋势: {stock['volume_trend']}\n"
                fundamental_info += f"RSI: {stock['rsi']:.2f}\n"
                fundamental_info += f"MACD: {stock['macd']:.4f}\n"
                fundamental_info += "-" * 50 + "\n"
            
            # 构建基本面分析的系统提示词
            system_prompt = f"""你是一个专业的基本面分析师。请基于提供的股票数据进行{analysis_params['type']}分析。

分析要求：
- 分析类型：{analysis_params['type']}
- 时间周期：{analysis_params['time_period']}
- 包含宏观分析：{analysis_params.get('include_macro', False)}
- 包含行业分析：{analysis_params.get('include_industry', False)}
- 包含竞争对手分析：{analysis_params.get('include_competitors', False)}
- 深度风险评估：{analysis_params.get('risk_assessment', False)}

请按以下结构进行分析：

## 1. 财务健康度分析
- 基于价格波动率和成交量分析公司稳定性
- 通过技术指标判断资金流向和投资者信心

## 2. 估值分析  
- 分析当前价格相对于52周区间的位置
- 评估价格趋势和估值合理性

## 3. 成长性分析
- 基于价格趋势强度分析成长潜力
- 结合成交量趋势判断市场关注度

## 4. 风险评估
- 分析价格波动率风险
- 评估技术指标显示的风险信号

## 5. 投资建议
- 综合基本面因素给出投资建议
- 建议合适的投资策略和风险控制措施

请用专业、客观的语言进行分析，并提供具体的数据支撑。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": fundamental_info}
            ]
            
            print("发送基本面分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print("基本面分析生成成功")
                return analysis_text
            else:
                print("基本面分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成基本面分析失败: {str(e)}")
            return None

    def generate_sector_rotation_analysis(self, sector_data: list) -> Optional[str]:
        """
        生成板块轮动分析
        
        Args:
            sector_data: 板块数据列表
            
        Returns:
            板块轮动分析文本，失败时返回None
        """
        try:
            print("开始生成板块轮动分析...")
            
            # 构建板块轮动分析数据
            sector_info = "板块轮动分析：\n\n"
            for stock in sector_data:
                sector_info += f"股票名称: {stock['name']}\n"
                sector_info += f"股票代码: {stock['code']}\n"
                sector_info += f"日涨跌幅: {stock['daily_change']:.2f}%\n"
                sector_info += f"周涨跌幅: {stock['weekly_change']:.2f}%\n"
                sector_info += f"月涨跌幅: {stock['monthly_change']:.2f}%\n"
                sector_info += f"季度涨跌幅: {stock['quarterly_change']:.2f}%\n"
                sector_info += f"量比: {stock['volume_ratio']:.2f}\n"
                sector_info += f"动量指标: {stock['momentum']:.2f}%\n"
                sector_info += "-" * 40 + "\n"
            
            system_prompt = """你是一个专业的板块轮动分析师。请基于提供的多只股票在不同时间周期的表现数据，分析当前的板块轮动情况。

请按以下结构进行分析：

## 1. 板块表现排名
- 按不同时间周期（日、周、月、季）对股票表现进行排名
- 识别强势板块和弱势板块

## 2. 轮动趋势分析
- 分析板块轮动的时间节点和规律
- 识别资金流向和热点板块转换

## 3. 动量分析
- 基于动量指标和量比分析板块活跃度
- 预测可能的轮动方向

## 4. 投资策略建议
- 推荐当前应关注的强势板块
- 建议板块配置比例和轮动策略
- 提供进出时机建议

请用专业的语言分析，并基于数据给出具体的投资建议。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sector_info}
            ]
            
            print("发送板块轮动分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print("板块轮动分析生成成功")
                return analysis_text
            else:
                print("板块轮动分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成板块轮动分析失败: {str(e)}")
            return None

    def generate_trend_strength_analysis(self, trend_data: list) -> Optional[str]:
        """
        生成趋势强度分析
        
        Args:
            trend_data: 趋势数据列表
            
        Returns:
            趋势强度分析文本，失败时返回None
        """
        try:
            print("开始生成趋势强度分析...")
            
            # 构建趋势强度分析数据
            trend_info = "趋势强度分析：\n\n"
            for stock in trend_data:
                trend_info += f"股票名称: {stock['name']}\n"
                trend_info += f"股票代码: {stock['code']}\n"
                trend_info += f"趋势方向: {stock['trend_direction']}\n"
                trend_info += f"趋势强度: {stock['trend_strength']:.2f}\n"
                trend_info += f"支撑位: {stock['support_level']:.2f}\n"
                trend_info += f"阻力位: {stock['resistance_level']:.2f}\n"
                trend_info += f"突破潜力: {stock['breakout_potential']}\n"
                trend_info += f"成交量确认: {'是' if stock['volume_confirmation'] else '否'}\n"
                trend_info += "-" * 40 + "\n"
            
            system_prompt = """你是一个专业的趋势分析师。请基于提供的趋势强度数据，分析各股票的趋势特征和投资机会。

请按以下结构进行分析：

## 1. 趋势强度排名
- 按趋势强度对股票进行排名
- 识别最强势和最弱势的股票

## 2. 支撑阻力分析
- 分析各股票的支撑阻力位有效性
- 识别关键的价格区间

## 3. 突破机会分析
- 评估各股票的突破潜力
- 结合成交量确认判断突破可信度

## 4. 趋势交易策略
- 基于趋势强度推荐交易策略
- 提供进场点位和止损建议
- 预测趋势可能的持续时间

## 5. 风险提示
- 识别趋势反转的早期信号
- 提醒关注的风险点

请结合技术分析理论，用专业的语言进行分析。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": trend_info}
            ]
            
            print("发送趋势强度分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print("趋势强度分析生成成功")
                return analysis_text
            else:
                print("趋势强度分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成趋势强度分析失败: {str(e)}")
            return None

    def generate_single_stock_analysis(self, detailed_data: Dict[str, Any]) -> Optional[str]:
        """
        生成单股深度分析
        
        Args:
            detailed_data: 详细的单股数据
            
        Returns:
            单股分析文本，失败时返回None
        """
        try:
            print(f"开始生成 {detailed_data['name']} 的单股分析...")
            
            # 构建单股分析数据
            stock_info = f"单股深度分析 - {detailed_data['name']}：\n\n"
            stock_info += f"股票代码: {detailed_data['code']}\n"
            stock_info += f"分析深度: {detailed_data['analysis_depth']}\n\n"
            
            # 价格数据
            price_data = detailed_data['price_data']
            stock_info += "价格数据：\n"
            stock_info += f"当前价格: {price_data['current']:.2f}\n"
            stock_info += f"52周最高: {price_data['high_52w']:.2f}\n"
            stock_info += f"52周最低: {price_data['low_52w']:.2f}\n"
            stock_info += f"30日均价: {price_data['avg_price_30d']:.2f}\n"
            stock_info += f"价格波动率: {price_data['volatility']:.2f}%\n\n"
            
            # 成交量数据
            volume_data = detailed_data['volume_data']
            stock_info += "成交量数据：\n"
            stock_info += f"当前成交量: {volume_data['current']:,.0f}\n"
            stock_info += f"30日平均成交量: {volume_data['avg_volume_30d']:,.0f}\n"
            stock_info += f"成交量趋势: {volume_data['volume_trend']}\n\n"
            
            # 技术指标
            tech_indicators = detailed_data['technical_indicators']
            stock_info += "技术指标：\n"
            stock_info += f"RSI: {tech_indicators['rsi']:.2f}\n"
            stock_info += f"MACD: {tech_indicators['macd']:.4f}\n"
            stock_info += f"MA5: {tech_indicators['ma5']:.2f}\n"
            stock_info += f"MA20: {tech_indicators['ma20']:.2f}\n"
            stock_info += f"布林带上轨: {tech_indicators['bollinger_upper']:.2f}\n"
            stock_info += f"布林带下轨: {tech_indicators['bollinger_lower']:.2f}\n\n"
            
            # 趋势分析
            trend_analysis = detailed_data['trend_analysis']
            stock_info += "趋势分析：\n"
            stock_info += f"趋势方向: {trend_analysis['direction']}\n"
            stock_info += f"趋势强度: {trend_analysis['strength']:.2f}\n"
            stock_info += f"支撑位: {trend_analysis['support_resistance']['support']:.2f}\n"
            stock_info += f"阻力位: {trend_analysis['support_resistance']['resistance']:.2f}\n"
            
            # 根据分析深度调整系统提示词
            if detailed_data['analysis_depth'] == "快速分析":
                analysis_sections = "技术面分析、短期走势判断、交易建议"
            elif detailed_data['analysis_depth'] == "深度分析":
                analysis_sections = "技术面分析、基本面推测、中期趋势判断、风险评估、详细交易策略"
            else:  # 全面评估
                analysis_sections = "全面技术分析、基本面综合评估、多时间框架分析、风险收益比分析、长中短期策略、资金管理建议"
            
            system_prompt = f"""你是一个专业的股票分析师。请对 {detailed_data['name']} 进行{detailed_data['analysis_depth']}。

分析要求包含：{analysis_sections}

请按以下结构进行分析：

## 1. 股票概况
- 当前价格位置分析（相对52周区间）
- 近期表现总结

## 2. 技术分析
- 技术指标解读（RSI、MACD、移动平均线、布林带）
- 支撑阻力位分析
- 趋势强度和方向判断

## 3. 成交量分析
- 成交量趋势变化
- 量价关系分析
- 资金流向判断

## 4. 风险评估
- 价格波动风险
- 技术风险信号
- 关键风险点位

## 5. 投资建议
- 具体的买卖建议
- 目标价位设定
- 止损点位建议
- 适合的投资周期

请提供专业、详细的分析，并给出具体的操作建议。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": stock_info}
            ]
            
            print("发送单股分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print(f"{detailed_data['name']} 单股分析生成成功")
                return analysis_text
            else:
                print("单股分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成单股分析失败: {str(e)}")
            return None

    def generate_market_insights(self, market_data: Dict[str, Any]) -> Optional[str]:
        """
        生成市场洞察
        
        Args:
            market_data: 市场数据
            
        Returns:
            市场洞察文本，失败时返回None
        """
        try:
            insight_type = market_data['insight_type']
            print(f"开始生成市场洞察: {insight_type}")
            
            # 构建市场洞察数据
            market_info = f"市场洞察分析 - {insight_type}：\n\n"
            
            # 市场概况
            summary = market_data['market_summary']
            market_info += "市场概况：\n"
            market_info += f"总股票数: {summary['total_stocks']}\n"
            market_info += f"上涨股票: {summary['rising_stocks']}\n"
            market_info += f"下跌股票: {summary['falling_stocks']}\n"
            market_info += f"平盘股票: {summary['flat_stocks']}\n"
            market_info += f"市场宽度: {summary['market_breadth']:.2%}\n\n"
            
            # 板块表现
            market_info += "板块表现前5名：\n"
            for i, stock in enumerate(market_data['sector_performance'][:5], 1):
                market_info += f"{i}. {stock['name']}: 日涨跌{stock['daily_change']:+.2f}%, "
                market_info += f"周涨跌{stock['weekly_change']:+.2f}%, 月涨跌{stock['monthly_change']:+.2f}%\n"
            market_info += "\n"
            
            # 市场广度指标
            breadth = market_data['market_breadth']
            market_info += "市场广度指标：\n"
            market_info += f"涨跌比率: {breadth['advance_decline_ratio']:.2%}\n"
            market_info += f"市场强度: {breadth['market_strength']:.1f}\n\n"
            
            # 情绪指标
            sentiment = market_data['sentiment_indicators']
            market_info += "市场情绪指标：\n"
            market_info += f"高成交量比例: {sentiment['high_volume_ratio']:.2%}\n"
            market_info += f"高波动率比例: {sentiment['high_volatility_ratio']:.2%}\n"
            market_info += f"市场活跃度: {sentiment['market_activity_level']:.2%}\n"
            
            # 根据洞察类型调整分析重点
            if insight_type == "市场趋势预测":
                focus = "基于当前数据预测未来1-3个月的市场趋势，识别关键转折点"
            elif insight_type == "热点板块分析":
                focus = "识别当前和未来的热点板块，分析资金轮动规律"
            elif insight_type == "资金流向分析":
                focus = "分析主力资金流向，判断增量资金和存量资金的配置偏好"
            else:  # 情绪指标分析
                focus = "分析投资者情绪变化，判断市场恐慌和贪婪程度"
            
            system_prompt = f"""你是一个资深的市场分析师。请基于提供的市场数据进行{insight_type}分析。

分析重点：{focus}

请按以下结构进行分析：

## 1. 市场现状分析
- 整体市场表现评估
- 市场宽度和参与度分析

## 2. 板块轮动分析
- 强势板块识别
- 资金流向特征
- 板块轮动规律

## 3. 市场情绪解读
- 投资者情绪状态判断
- 恐慌/贪婪指数评估
- 市场活跃度分析

## 4. 趋势预测
- 短期趋势判断（1-4周）
- 中期趋势预测（1-3个月）
- 关键节点识别

## 5. 投资策略建议
- 基于当前市场状态的投资建议
- 风险控制要点
- 关注重点和时机选择

请结合宏观经济和市场技术面，提供专业的市场洞察。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": market_info}
            ]
            
            print("发送市场洞察分析请求...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            
            if response.choices and response.choices[0].message:
                analysis_text = response.choices[0].message.content.strip()
                print("市场洞察分析生成成功")
                return analysis_text
            else:
                print("市场洞察分析响应为空")
                return None
                
        except Exception as e:
            print(f"生成市场洞察失败: {str(e)}")
            return None
