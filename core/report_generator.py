"""
报告生成模块

负责生成HTML格式的股票分析报告
"""

import os
from string import Template
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
import pytz
from utils.logger import get_logger
from utils.helpers import generate_table_row

logger = get_logger(__name__)


class ReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.template_path = 'static/templates/report_template.html'
        self.css_path = 'static/css/report.css'
        logger.info("报告生成器已初始化")
    
    def generate_report(self, stock_analyses: List[Tuple[str, Dict[str, Any]]], 
                       pool_ai_analysis: Optional[str] = None) -> str:
        """
        生成完整的HTML报告
        
        Args:
            stock_analyses: 股票分析数据列表 [(股票代码, 分析数据)]
            pool_ai_analysis: 股票池AI分析结果
            
        Returns:
            HTML报告内容
        """
        logger.info("开始生成HTML报告...")
        
        try:
            # 检查和读取模板文件
            css_content = self._load_css_content()
            html_template = self._load_html_template()
            
            # 生成报告时间 - 使用中国时区
            tz = pytz.timezone('Asia/Shanghai')
            # 如果系统时间不准确，可以使用UTC时间转换
            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            china_time = utc_now.astimezone(tz)
            current_time = china_time.strftime('%Y年%m月%d日 %H时%M分%S秒')
            
            logger.debug(f"报告生成时间: {current_time}")
            
            # 生成股票分析内容
            stock_contents = []
            for code, analysis_data in stock_analyses:
                stock_content = self._generate_stock_analysis_html(code, analysis_data)
                stock_contents.append(stock_content)
            
            # 生成整体AI分析
            pool_ai_html = ""
            if pool_ai_analysis:
                pool_ai_html = self._generate_structured_ai_analysis(pool_ai_analysis)
            
            # 组合完整内容
            full_content = pool_ai_html + '\n'.join(stock_contents)
            
            # 使用模板生成最终HTML
            template = Template(html_template)
            html_content = template.substitute(
                styles=css_content,
                generate_time=current_time,
                content=full_content
            )
            
            # 手动替换JSON中的时间占位符
            html_content = html_content.replace('REPLACE_GENERATE_TIME', current_time)
            
            logger.info("HTML报告生成完成")
            return html_content
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {str(e)}")
            raise
    
    def _load_css_content(self) -> str:
        """加载CSS样式内容"""
        try:
            if os.path.exists(self.css_path):
                with open(self.css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                logger.debug("成功加载CSS样式文件")
                return css_content
            else:
                logger.warning(f"CSS文件不存在: {self.css_path}，使用默认样式")
                return self._get_default_css()
        except Exception as e:
            logger.error(f"加载CSS文件失败: {str(e)}")
            return self._get_default_css()
    
    def _load_html_template(self) -> str:
        """加载HTML模板文件"""
        try:
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"模板文件不存在: {self.template_path}")
            
            with open(self.template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            logger.debug("成功加载HTML模板文件")
            return html_template
            
        except Exception as e:
            logger.error(f"加载HTML模板失败: {str(e)}")
            raise
    
    def _generate_stock_analysis_html(self, code: str, analysis_data: Dict[str, Any]) -> str:
        """
        生成单个股票的分析HTML
        
        Args:
            code: 股票代码
            analysis_data: 分析数据
            
        Returns:
            股票分析HTML内容
        """
        try:
            # 获取股票名称
            basic_data = analysis_data.get('基础数据', {})
            stock_name = basic_data.get('股票名称', code)
            
            # 检查是否有错误
            if '数据状态' in basic_data and basic_data['数据状态'] != '正常':
                return self._generate_error_stock_html(code, stock_name, basic_data)
            
            # 生成正常的股票分析HTML
            return self._generate_normal_stock_html(code, stock_name, analysis_data)
            
        except Exception as e:
            logger.error(f"生成股票 {code} 分析HTML失败: {str(e)}")
            return self._generate_error_stock_html(code, code, {'数据状态': f'生成失败: {str(e)}'})
    
    def _generate_normal_stock_html(self, code: str, stock_name: str, 
                                   analysis_data: Dict[str, Any]) -> str:
        """生成正常股票的分析HTML"""
        # 生成基础数据HTML
        basic_data_html = self._generate_basic_data_html(analysis_data.get('基础数据', {}))
        
        # 生成交易信号HTML
        signals_html = self._generate_signals_html(analysis_data.get('技术分析建议', []))
        
        # 组合股票完整内容
        stock_content = f"""
        <div class="stock-container">
            <h2>{stock_name} ({code}) 分析报告</h2>
            
            <div class="section-divider">
                <h2>基础数据</h2>
            </div>
            
            <div class="data-grid">
                {basic_data_html}
            </div>
            
            <div class="section-divider">
                <h2>交易信号</h2>
            </div>
            
            {signals_html}
        </div>
        """
        
        return stock_content
    
    def _generate_error_stock_html(self, code: str, stock_name: str, 
                                  basic_data: Dict[str, Any]) -> str:
        """生成错误股票的HTML"""
        error_status = basic_data.get('数据状态', '未知错误')
        error_info = basic_data.get('错误信息', '')
        
        stock_content = f"""
        <div class="stock-container">
            <h2>{stock_name} ({code}) 分析报告</h2>
            <div class="error-message">
                <h3>数据获取失败</h3>
                <p>无法获取股票 {stock_name} ({code}) 的数据</p>
                <p>错误信息: {error_status}</p>
                {f'<p>详细信息: {error_info}</p>' if error_info else ''}
                <p>请检查股票代码格式是否正确：</p>
                <ul>
                    <li>上交所: sh000001 (上证指数), sh600036 (招商银行)</li>
                    <li>深交所: sz399001 (深证成指), sz000001 (平安银行), sz002640 (跨境通)</li>
                    <li>港股: 01357.HK (美图公司)</li>
                </ul>
            </div>
        </div>
        """
        
        return stock_content
    
    def _generate_basic_data_html(self, basic_data: Dict[str, Any]) -> str:
        """生成基础数据HTML"""
        try:
            basic_data_html = f"""
            <div class="indicator-section">
                <h3>基础数据</h3>
                <table class="data-table">
                    <tr>
                        <th>指标</th>
                        <th>数值</th>
                    </tr>
                    {''.join(generate_table_row(k, v) for k, v in basic_data.items())}
                </table>
            </div>
            """
            return basic_data_html
        except Exception as e:
            logger.error(f"生成基础数据HTML失败: {str(e)}")
            return "<div class='error-message'>基础数据显示错误</div>"
    
    def _generate_signals_html(self, signals: List[str]) -> str:
        """生成交易信号HTML"""
        try:
            signals_html = f"""
            <div class="indicator-section">
                <h3>交易信号</h3>
                <ul class="signal-list">
                    {''.join(f'<li>{signal}</li>' for signal in signals)}
                </ul>
            </div>
            """
            return signals_html
        except Exception as e:
            logger.error(f"生成交易信号HTML失败: {str(e)}")
            return "<div class='error-message'>交易信号显示错误</div>"
    
    def _generate_structured_ai_analysis(self, ai_text: str) -> str:
        """生成结构化的AI分析HTML"""
        if not ai_text:
            return ""
        
        try:
            # 解析AI文本的各个部分
            sections = self._parse_ai_sections(ai_text)
            
            html_parts = []
            html_parts.append('<div class="ai-pool-analysis-container">')
            html_parts.append('<div class="section-divider"><h2>🤖 AI股票池整体策略分析</h2></div>')
            
            # 生成各个分析部分
            section_generators = {
                'overall': ('📊 技术面整体分析', '🎯'),
                'industry': ('🏭 行业技术特征分析', '📈'),
                'stocks': ('📋 个股技术深度分析', '🔍'),
                'strategy': ('🎯 投资策略建议', '💼'),
                'risks': ('⚖️ 技术面机会与风险', '🎲'),
                'sentiment': ('😊 技术情绪评分', '📊'),
                'timeline': ('⏰ 技术操作时间窗口', '📅')
            }
            
            for section_key, (title, icon) in section_generators.items():
                if section_key in sections:
                    html_parts.append(self._generate_ai_section_html(
                        title, icon, sections[section_key], section_key
                    ))
            
            html_parts.append('</div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"生成AI分析HTML失败: {str(e)}")
            return f"<div class='error-message'>AI分析显示错误: {str(e)}</div>"
    
    def _parse_ai_sections(self, ai_text: str) -> Dict[str, str]:
        """解析AI文本的各个部分"""
        sections = {}
        
        try:
            import re
            
            # 使用正则表达式提取各个部分
            section_patterns = [
                ('overall', r'【1\. 技术面整体分析】([\s\S]+?)【2\.'),
                ('industry', r'【2\. 行业技术特征分析】([\s\S]+?)【3\.'),
                ('stocks', r'【3\. 个股技术深度分析】([\s\S]+?)【4\.'),
                ('strategy', r'【4\. 投资策略建议】([\s\S]+?)【5\.'),
                ('risks', r'【5\. 技术面机会与风险】([\s\S]+?)【6\.'),
                ('sentiment', r'【6\. 技术情绪评分】([\s\S]+?)【7\.'),
                ('timeline', r'【7\. 技术操作时间窗口】([\s\S]+?)(?:\n\n|$)')
            ]
            
            for section_key, pattern in section_patterns:
                match = re.search(pattern, ai_text)
                if match:
                    sections[section_key] = match.group(1).strip()
            
            return sections
            
        except Exception as e:
            logger.error(f"解析AI文本失败: {str(e)}")
            return {}
    
    def _generate_ai_section_html(self, title: str, icon: str, content: str, 
                                 section_type: str) -> str:
        """生成AI分析部分的HTML"""
        try:
            formatted_content = self._format_text_content(content)
            
            # 特殊处理个股分析部分
            if section_type == 'stocks':
                formatted_content = self._generate_stock_cards_html(content)
            elif section_type == 'sentiment':
                formatted_content = self._generate_sentiment_html(content)
            
            return f"""
            <div class="ai-section {section_type}-section">
                <div class="section-header">
                    <h3>{title}</h3>
                    <div class="section-icon">{icon}</div>
                </div>
                <div class="section-content">
                    {formatted_content}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"生成AI部分HTML失败: {str(e)}")
            return f"<div class='error-message'>部分内容显示错误</div>"
    
    def _generate_stock_cards_html(self, content: str) -> str:
        """生成个股分析卡片HTML"""
        try:
            import re
            
            # 解析个股分析
            stock_analyses = re.findall(r'\*([^(]+)\(([^)]+)\)：([\s\S]+?)(?=\*|$)', content)
            
            stock_cards = []
            for stock_name, stock_code, analysis in stock_analyses:
                # 解析各个字段
                signal_strength = re.search(r'信号强度[：:]\s*([^\n]+)', analysis)
                indicators = re.search(r'指标组合[：:]\s*([^\n]+)', analysis)
                pattern = re.search(r'形态识别[：:]\s*([^\n]+)', analysis)
                risk = re.search(r'风险点[：:]\s*([^\n]+)', analysis)
                opportunity = re.search(r'机会点[：:]\s*([^\n]+)', analysis)
                
                stock_card = f"""
                <div class="stock-analysis-card">
                    <div class="stock-header">
                        <h4>{stock_name.strip()} ({stock_code.strip()})</h4>
                        <div class="stock-score">{signal_strength.group(1).strip() if signal_strength else 'N/A'}</div>
                    </div>
                    <div class="stock-details">
                        <div class="detail-item">
                            <span class="label">📊 指标组合:</span>
                            <span class="value">{indicators.group(1).strip() if indicators else 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">📈 形态识别:</span>
                            <span class="value">{pattern.group(1).strip() if pattern else 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">⚠️ 风险点:</span>
                            <span class="value risk">{risk.group(1).strip() if risk else 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">💡 机会点:</span>
                            <span class="value opportunity">{opportunity.group(1).strip() if opportunity else 'N/A'}</span>
                        </div>
                    </div>
                </div>
                """
                stock_cards.append(stock_card)
            
            if not stock_cards:
                return f"<div class='analysis-text'>{self._format_text_content(content)}</div>"
            
            return f"<div class='stock-cards-grid'>{''.join(stock_cards)}</div>"
            
        except Exception as e:
            logger.error(f"生成个股卡片HTML失败: {str(e)}")
            return f"<div class='analysis-text'>{self._format_text_content(content)}</div>"
    
    def _generate_sentiment_html(self, content: str) -> str:
        """生成情绪分析HTML"""
        try:
            import re
            
            sentiment_score = re.search(r'综合评分[：:]\s*([-+]?\d*\.?\d+)', content)
            score = sentiment_score.group(1) if sentiment_score else '0.0'
            
            # 根据分数确定情绪图标和颜色
            score_float = float(score)
            if score_float > 0.3:
                emotion_icon = "😊"
                emotion_class = "positive"
            elif score_float < -0.3:
                emotion_icon = "😟"
                emotion_class = "negative"
            else:
                emotion_icon = "😐"
                emotion_class = "neutral"
            
            return f"""
            <div class="sentiment-display">
                <div class="sentiment-score {emotion_class}">
                    <span class="score-icon">{emotion_icon}</span>
                    <span class="score-value">{score}</span>
                </div>
            </div>
            <div class="analysis-text">{self._format_text_content(content)}</div>
            """
        except Exception as e:
            logger.error(f"生成情绪分析HTML失败: {str(e)}")
            return f"<div class='analysis-text'>{self._format_text_content(content)}</div>"
    
    def _format_text_content(self, content: str) -> str:
        """格式化文本内容，处理换行和特殊字符"""
        if not content:
            return ""
        
        try:
            # 先处理换行符，将其转换为HTML换行标签
            content = content.replace('\n', '___BR___')
            
            # 替换特殊字符（除了我们的临时标记）
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # 将临时标记转换回HTML换行标签
            content = content.replace('___BR___', '<br>')
            
            return content
        except Exception as e:
            logger.error(f"格式化文本内容失败: {str(e)}")
            return str(content)
    
    def _get_default_css(self) -> str:
        """获取默认CSS样式"""
        return """
        /* 默认样式 */
        body { font-family: Arial, sans-serif; margin: 20px; }
        .stock-container { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; }
        .section-divider h2 { color: #333; border-bottom: 2px solid #007bff; }
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th, .data-table td { padding: 8px; border: 1px solid #ddd; }
        .positive { color: green; }
        .negative { color: red; }
        .neutral { color: #666; }
        .error-message { color: red; padding: 10px; background: #ffe6e6; }
        """ 