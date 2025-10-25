#!/bin/bash
# 预热缓存脚本

echo "🔥 预热缓存..."

# 创建缓存目录
mkdir -p data/cache

# 预热股票数据缓存
echo "📊 预热股票数据缓存..."
python3 -c "
from ashare.data import StockDataFetcher
from ashare.logging import get_logger

logger = get_logger('warmup')
logger.info('开始预热缓存...')

# 预热一些常用股票的数据
stocks = ['sh000001', 'sz399001', 'sh600036', 'sz000001']
fetcher = StockDataFetcher()

for stock in stocks:
    try:
        data = fetcher.get_stock_data(stock, count=100)
        logger.info(f'预热完成: {stock}')
    except Exception as e:
        logger.warning(f'预热失败: {stock} - {e}')

logger.info('缓存预热完成')
"

echo "✅ 缓存预热完成"
