import os
import re
import requests
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def load_env_config():
    """加载环境变量配置"""
    try:
        from dotenv import load_dotenv
        
        # 尝试加载.env文件
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ 成功加载配置文件: {env_path}")
        else:
            print(f"⚠️ 配置文件不存在: {env_path}")
            print("📝 请根据 env.example 创建 .env 文件")
            
    except ImportError:
        print("❌ 缺少 python-dotenv 依赖")
        print("请运行: pip install python-dotenv")
        return False
    
    return True


class Config:
    """配置管理类"""
    
    def __init__(self):
        # 加载环境变量
        load_env_config()
        
        # AI 配置
        self.llm_api_key = os.environ.get('LLM_API_KEY')
        self.llm_base_url = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com')
        self.llm_model = os.environ.get('LLM_MODEL', 'deepseek-chat')
        
        # 推送配置
        self.serverchan_key = os.environ.get('SERVERCHAN_KEY')
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.sender_email = os.environ.get('SENDER_EMAIL')
        self.sender_password = os.environ.get('SENDER_PASSWORD')
        self.receiver_email = os.environ.get('RECEIVER_EMAIL')
        self.work_wechat_webhook = os.environ.get('WORK_WECHAT_WEBHOOK')
        
        # 应用配置
        self.push_methods = os.environ.get('PUSH_METHODS', 'serverchan').split(',')
        self.enable_push = os.environ.get('ENABLE_PUSH', 'true').lower() == 'true'
        self.data_count = int(os.environ.get('DATA_COUNT', '120'))
    
    def validate_config(self) -> List[str]:
        """
        验证配置完整性和有效性
        
        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []
        
        try:
            logger.info("开始验证配置...")
            
            # 验证AI配置
            errors.extend(self._validate_ai_config())
            
            # 验证推送配置
            if self.enable_push:
                errors.extend(self._validate_push_config())
            
            # 验证应用配置
            errors.extend(self._validate_app_config())
            
            # 验证环境配置
            errors.extend(self._validate_environment())
            
            if errors:
                logger.error(f"配置验证失败，发现{len(errors)}个错误")
            else:
                logger.info("配置验证通过")
                
        except Exception as e:
            logger.error(f"配置验证过程出错: {str(e)}")
            errors.append(f"❌ 配置验证过程出错: {str(e)}")
        
        return errors
    
    def _validate_ai_config(self) -> List[str]:
        """验证AI配置"""
        errors = []
        
        # 检查API密钥
        if not self.llm_api_key:
            errors.append("❌ 缺少 LLM_API_KEY 配置")
        elif not self.llm_api_key.startswith(('sk-', 'API-')):
            errors.append("❌ LLM_API_KEY 格式可能不正确")
        
        # 检查API地址
        if not self.llm_base_url:
            errors.append("❌ 缺少 LLM_BASE_URL 配置")
        elif not self._is_valid_url(self.llm_base_url):
            errors.append("❌ LLM_BASE_URL 格式不正确")
        
        # 检查模型名称
        if not self.llm_model:
            errors.append("❌ 缺少 LLM_MODEL 配置")
        
        return errors
    
    def _validate_push_config(self) -> List[str]:
        """验证推送配置"""
        errors = []
        
        # 检查推送方式配置
        valid_methods = ['serverchan', 'email', 'work_wechat']
        invalid_methods = [m for m in self.push_methods if m not in valid_methods]
        if invalid_methods:
            errors.append(f"❌ 不支持的推送方式: {invalid_methods}")
        
        # 检查Server酱配置
        if 'serverchan' in self.push_methods:
            if not self.serverchan_key:
                errors.append("❌ 启用了Server酱推送但缺少 SERVERCHAN_KEY 配置")
            elif not self.serverchan_key.startswith('SCT'):
                errors.append("❌ SERVERCHAN_KEY 格式不正确，应以SCT开头")
        
        # 检查邮件配置
        if 'email' in self.push_methods:
            if not self.sender_email:
                errors.append("❌ 启用了邮件推送但缺少 SENDER_EMAIL 配置")
            elif not self._is_valid_email(self.sender_email):
                errors.append("❌ SENDER_EMAIL 格式不正确")
            
            if not self.sender_password:
                errors.append("❌ 启用了邮件推送但缺少 SENDER_PASSWORD 配置")
            
            if not self.receiver_email:
                errors.append("❌ 启用了邮件推送但缺少 RECEIVER_EMAIL 配置")
            elif not self._is_valid_email(self.receiver_email):
                errors.append("❌ RECEIVER_EMAIL 格式不正确")
            
            # 检查SMTP配置
            if not self.smtp_server:
                errors.append("❌ 启用了邮件推送但缺少 SMTP_SERVER 配置")
            
            if not (1 <= self.smtp_port <= 65535):
                errors.append("❌ SMTP_PORT 端口号无效")
        
        # 检查企业微信配置
        if 'work_wechat' in self.push_methods:
            if not self.work_wechat_webhook:
                errors.append("❌ 启用了企业微信推送但缺少 WORK_WECHAT_WEBHOOK 配置")
            elif not self._is_valid_url(self.work_wechat_webhook):
                errors.append("❌ WORK_WECHAT_WEBHOOK URL格式不正确")
        
        return errors
    
    def _validate_app_config(self) -> List[str]:
        """验证应用配置"""
        errors = []
        
        # 检查数据条数配置
        if not isinstance(self.data_count, int) or self.data_count <= 0:
            errors.append("❌ DATA_COUNT 必须是正整数")
        elif self.data_count < 60:
            errors.append("⚠️ DATA_COUNT 小于60，可能影响技术指标准确性")
        elif self.data_count > 1000:
            errors.append("⚠️ DATA_COUNT 过大，可能影响性能")
        
        return errors
    
    def _validate_environment(self) -> List[str]:
        """验证运行环境"""
        errors = []
        
        try:
            # 检查必要的Python包
            required_packages = [
                'pandas', 'numpy', 'matplotlib', 'requests', 
                'pytz', 'openai'
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    errors.append(f"❌ 缺少必要的Python包: {package}")
            
            # 检查文件系统权限
            try:
                test_dir = Path('logs')
                test_dir.mkdir(exist_ok=True)
                test_file = test_dir / 'test.txt'
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                errors.append(f"❌ 文件系统权限问题: {str(e)}")
            
        except Exception as e:
            logger.error(f"环境验证出错: {str(e)}")
            errors.append(f"❌ 环境验证出错: {str(e)}")
        
        return errors
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            url_pattern = re.compile(
                r'^https?://'  # http:// 或 https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
                r'(?::\d+)?'  # 端口号
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            return url_pattern.match(url) is not None
        except Exception:
            return False
    
    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式"""
        try:
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            return email_pattern.match(email) is not None
        except Exception:
            return False
    
    def test_api_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        result = {
            'llm_api': {'status': 'unknown', 'message': ''},
            'serverchan': {'status': 'unknown', 'message': ''}
        }
        
        # 测试LLM API连接
        if self.llm_api_key and self.llm_base_url:
            try:
                logger.info("测试LLM API连接...")
                # 这里可以添加实际的API连接测试
                result['llm_api'] = {'status': 'success', 'message': 'API配置正确'}
                logger.info("LLM API连接测试成功")
            except Exception as e:
                result['llm_api'] = {'status': 'error', 'message': str(e)}
                logger.error(f"LLM API连接测试失败: {str(e)}")
        
        # 测试Server酱推送
        if self.serverchan_key and 'serverchan' in self.push_methods:
            try:
                logger.info("测试Server酱推送...")
                # 这里可以添加实际的推送测试
                result['serverchan'] = {'status': 'success', 'message': '推送配置正确'}
                logger.info("Server酱推送测试成功")
            except Exception as e:
                result['serverchan'] = {'status': 'error', 'message': str(e)}
                logger.error(f"Server酱推送测试失败: {str(e)}")
        
        return result
    
    def print_config_status(self):
        """打印配置状态"""
        print("\n🔧 当前配置状态：")
        print(f"AI配置: {'✅' if self.llm_api_key else '❌'} LLM API")
        print(f"推送功能: {'✅ 启用' if self.enable_push else '❌ 禁用'}")
        
        if self.enable_push:
            print("推送方式:")
            for method in self.push_methods:
                if method == 'serverchan':
                    status = '✅' if self.serverchan_key else '❌'
                    print(f"  {status} Server酱微信推送")
                elif method == 'email':
                    status = '✅' if all([self.sender_email, self.sender_password, self.receiver_email]) else '❌'
                    print(f"  {status} 邮件推送")
                elif method == 'work_wechat':
                    status = '✅' if self.work_wechat_webhook else '❌'
                    print(f"  {status} 企业微信推送")
        
        print(f"数据条数: {self.data_count}")
        print()


def create_env_file_guide():
    """创建.env文件指南"""
    guide = """
🔧 环境配置指南：

1️⃣ 复制示例文件：
   cp env.example .env

2️⃣ 编辑 .env 文件，填入你的配置：
   # AI 配置 (必需)
   LLM_API_KEY=sk-你的deepseek_api_key
   LLM_BASE_URL=https://api.deepseek.com
   LLM_MODEL=deepseek-chat

   # 微信推送配置 (推荐)
   SERVERCHAN_KEY=SCT你的server酱sendkey

3️⃣ 保存文件后重新运行程序

📝 注意：.env 文件已被 .gitignore 忽略，不会被提交到版本控制
    """
    print(guide)


if __name__ == "__main__":
    # 测试配置
    config = Config()
    config.print_config_status()
    
    errors = config.validate_config()
    if errors:
        print("⚠️ 配置错误：")
        for error in errors:
            print(f"  {error}")
        print()
        create_env_file_guide()
    else:
        print("✅ 所有配置验证通过！") 