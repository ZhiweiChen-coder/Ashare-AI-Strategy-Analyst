# MyTT 麦语言-通达信-同花顺指标实现    https://github.com/mpquant/MyTT
# V2.1 2021-6-6 新增 BARSLAST函数
# V2.2 2021-6-8 新增 SLOPE,FORCAST线性回归，和回归预测函数
  
import numpy as np; import pandas as pd

#------------------ 0级：核心工具函数 --------------------------------------------      
def RD(N,D=3):   return np.round(N,D)        #四舍五入取3位小数 
def RET(S,N=1):  return np.array(S)[-N]      #返回序列倒数第N个值,默认返回最后一个
def ABS(S):      return np.abs(S)            #返回N的绝对值
def MAX(S1,S2):  return np.maximum(S1,S2)    #序列max
def MIN(S1,S2):  return np.minimum(S1,S2)    #序列min
         
def MA(S,N):           #求序列的N日平均值，返回序列                    
    return pd.Series(S).rolling(N).mean().values

def REF(S, N=1):       #对序列整体下移动N,返回序列(shift后会产生NAN)    
    return pd.Series(S).shift(N).values  

def DIFF(S, N=1):      #前一个值减后一个值,前面会产生nan 
    return pd.Series(S).diff(N)  #np.diff(S)直接删除nan，会少一行

def STD(S,N):           #求序列的N日标准差，返回序列    
    return  pd.Series(S).rolling(N).std(ddof=0).values     

def IF(S_BOOL,S_TRUE,S_FALSE):          #序列布尔判断 res=S_TRUE if S_BOOL==True  else  S_FALSE
    return np.where(S_BOOL, S_TRUE, S_FALSE)

def SUM(S, N):                          #对序列求N天累计和，返回序列         
    return pd.Series(S).rolling(N).sum().values

def HHV(S,N):                           # HHV(C, 5)  # 最近5天收盘最高价        
    return pd.Series(S).rolling(N).max().values

def LLV(S,N):                           # LLV(C, 5)  # 最近5天收盘最低价     
    return pd.Series(S).rolling(N).min().values

def EMA(S,N):         #指数移动平均,为了精度 S>4*N  EMA至少需要120周期       
    return pd.Series(S).ewm(span=N, adjust=False).mean().values    

def SMA(S, N, M=1):   #中国式的SMA,至少需要120周期才精确         
    K = pd.Series(S).rolling(N).mean()    #先求出平均值 (下面如果有不用循环的办法，能提高性能，望告知)
    for i in range(N+1, len(S)):  K[i] = (M * S[i] + (N -M) * K[i-1]) / N  # 因为要取K[i-1]，所以 range(N+1, len(S))        
    return K

def AVEDEV(S,N):      #平均绝对偏差  (序列与其平均值的绝对差的平均值)   
    avedev=pd.Series(S).rolling(N).apply(lambda x: (np.abs(x - x.mean())).mean())    
    return avedev.values

def SLOPE(S,N,RS=False):               #返S序列N周期回线性回归斜率 (默认只返回斜率,不返回整个直线序列)
    M=pd.Series(S[-N:]);   poly = np.polyfit(M.index, M.values,deg=1);    Y=np.polyval(poly, M.index); 
    if RS: return Y[1]-Y[0],Y
    return Y[1]-Y[0]

  
#------------------   1级：应用层函数(通过0级核心函数实现） ----------------------------------
def COUNT(S_BOOL, N):                  # COUNT(CLOSE>O, N):  最近N天满足S_BOO的天数  True的天数
    return SUM(S_BOOL,N)    

def EVERY(S_BOOL, N):                  # EVERY(CLOSE>O, 5)   最近N天是否都是True
    R=SUM(S_BOOL, N)
    return  IF(R==N, True, False)
  
def LAST(S_BOOL, A, B):                #从前A日到前B日一直满足S_BOOL条件   
    if A<B: A=B                        #要求A>B    例：LAST(CLOSE>OPEN,5,3)  5天前到3天前是否都收阳线     
    return S_BOOL[-A:-B].sum()==(A-B)  #返回单个布尔值    

def EXIST(S_BOOL, N=5):                # EXIST(CLOSE>3010, N=5)  n日内是否存在一天大于3000点
    R=SUM(S_BOOL,N)    
    return IF(R>0, True ,False)

def BARSLAST(S_BOOL):                  #上一次条件成立到当前的周期  
    M=np.argwhere(S_BOOL);             # BARSLAST(CLOSE/REF(CLOSE)>=1.1) 上一次涨停到今天的天数
    return len(S_BOOL)-int(M[-1])-1  if M.size>0 else -1

def FORCAST(S,N):                      #返S序列N周期回线性回归后的预测值
    K,Y=SLOPE(S,N,RS=True)
    return Y[-1]+K
  
def CROSS(S1,S2):                      #判断穿越 CROSS(MA(C,5),MA(C,10))               
    CROSS_BOOL=IF(S1>S2, True ,False)   
    return COUNT(CROSS_BOOL>0,2)==1    #上穿：昨天0 今天1   下穿：昨天1 今天0



#------------------   2级：技术指标函数(全部通过0级，1级函数实现） ------------------------------
def MACD(CLOSE,SHORT=12,LONG=26,M=9):            # EMA的关系，S取120日，和雪球小数点2位相同
    DIF = EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);  
    DEA = EMA(DIF,M);      MACD=(DIF-DEA)*2
    return RD(DIF),RD(DEA),RD(MACD)

def KDJ(CLOSE,HIGH,LOW, N=9,M1=3,M2=3):         # KDJ指标
    RSV = (CLOSE - LLV(LOW, N)) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    K = EMA(RSV, (M1*2-1));    D = EMA(K,(M2*2-1));        J=K*3-D*2
    return K, D, J

def RSI(CLOSE, N=24):      
    DIF = CLOSE-REF(CLOSE,1) 
    return RD(SMA(MAX(DIF,0), N) / SMA(ABS(DIF), N) * 100)

def OBV(CLOSE, VOLUME):                     # 能量潮指标
    """On-Balance Volume 能量潮指标"""
    obv = np.zeros_like(CLOSE, dtype=float)
    obv[0] = VOLUME[0]
    
    for i in range(1, len(CLOSE)):
        if CLOSE[i] > CLOSE[i-1]:      # 价格上涨
            obv[i] = obv[i-1] + VOLUME[i]
        elif CLOSE[i] < CLOSE[i-1]:    # 价格下跌
            obv[i] = obv[i-1] - VOLUME[i]
        else:                          # 价格不变
            obv[i] = obv[i-1]
    
    return RD(obv)

def ADL(HIGH, LOW, CLOSE, VOLUME):          # 累积/派发线
    """Accumulation/Distribution Line 累积/派发线"""
    adl = np.zeros_like(CLOSE, dtype=float)
    
    for i in range(len(CLOSE)):
        if HIGH[i] != LOW[i]:  # 避免除零
            mfm = ((CLOSE[i] - LOW[i]) - (HIGH[i] - CLOSE[i])) / (HIGH[i] - LOW[i])
            mfv = mfm * VOLUME[i]
            adl[i] = adl[i-1] + mfv if i > 0 else mfv
        else:
            adl[i] = adl[i-1] if i > 0 else 0
    
    return RD(adl)

def CMF(HIGH, LOW, CLOSE, VOLUME, N=20):    # 蔡金资金流量指标
    """Chaikin Money Flow 蔡金资金流量指标"""
    mfm = np.zeros_like(CLOSE, dtype=float)
    
    for i in range(len(CLOSE)):
        if HIGH[i] != LOW[i]:  # 避免除零
            mfm[i] = ((CLOSE[i] - LOW[i]) - (HIGH[i] - CLOSE[i])) / (HIGH[i] - LOW[i])
    
    mfv = mfm * VOLUME
    cmf = SUM(mfv, N) / SUM(VOLUME, N)
    
    return RD(cmf)

def TRIX(CLOSE, N=14, M=9):                 # 三重指数平滑平均线
    """TRIX三重指数平滑平均线指标"""
    tr1 = EMA(CLOSE, N)
    tr2 = EMA(tr1, N)  
    tr3 = EMA(tr2, N)
    trix = (tr3 - REF(tr3, 1)) / REF(tr3, 1) * 100
    trma = MA(trix, M)
    return RD(trix), RD(trma)

def DMA(CLOSE, N1=10, N2=50, M=10):         # 平行线差指标
    """DMA平行线差指标"""
    dif = MA(CLOSE, N1) - MA(CLOSE, N2)
    difma = MA(dif, M)
    return RD(dif), RD(difma)

# WR函数在后面已定义，删除重复

def CCI(CLOSE, HIGH, LOW, N=14):            # 顺势指标
    """Commodity Channel Index 顺势指标"""
    tp = (HIGH + LOW + CLOSE) / 3
    ma_tp = MA(tp, N)
    md = pd.Series(tp).rolling(N).apply(lambda x: np.mean(np.abs(x - x.mean()))).values
    cci = (tp - ma_tp) / (0.015 * md)
    return RD(cci)

def PSY(CLOSE, N=12, M=6):                  # 心理线
    """心理线指标"""
    psy = COUNT(CLOSE > REF(CLOSE, 1), N) / N * 100
    psyma = MA(psy, M)
    return RD(psy), RD(psyma)

def BIAS(CLOSE, N1=6, N2=12, N3=24):        # 乖离率
    """乖离率指标"""
    bias1 = (CLOSE - MA(CLOSE, N1)) / MA(CLOSE, N1) * 100
    bias2 = (CLOSE - MA(CLOSE, N2)) / MA(CLOSE, N2) * 100  
    bias3 = (CLOSE - MA(CLOSE, N3)) / MA(CLOSE, N3) * 100
    return RD(bias1), RD(bias2), RD(bias3)

def DMI(CLOSE, HIGH, LOW, N=14, M=6):       # 动向指标
    """方向性运动指标"""
    hd = HIGH - REF(HIGH, 1)
    ld = REF(LOW, 1) - LOW
    dmp = IF(hd > 0 & hd > ld, hd, 0)  
    dmm = IF(ld > 0 & ld > hd, ld, 0)
    
    tr1 = HIGH - LOW
    tr2 = ABS(HIGH - REF(CLOSE, 1))
    tr3 = ABS(REF(CLOSE, 1) - LOW) 
    tr = MAX(MAX(tr1, tr2), tr3)
    
    trsum = SMA(tr, N)
    dmpsum = SMA(dmp, N)
    dmmsum = SMA(dmm, N)
    
    pdi = dmpsum / trsum * 100
    mdi = dmmsum / trsum * 100
    dx = ABS(mdi - pdi) / (mdi + pdi) * 100
    adx = SMA(dx, M)
    adxr = (adx + REF(adx, M)) / 2
    
    return RD(pdi), RD(mdi), RD(adx), RD(adxr)

def VR(CLOSE, VOLUME, N=26):                # 成交量比率
    """Volume Ratio 成交量比率"""
    lc = REF(CLOSE, 1)
    up_vol = SUM(IF(CLOSE > lc, VOLUME, 0), N)
    down_vol = SUM(IF(CLOSE < lc, VOLUME, 0), N)
    eq_vol = SUM(IF(CLOSE == lc, VOLUME, 0), N)
    
    vr = (up_vol + eq_vol/2) / (down_vol + eq_vol/2) * 100
    return RD(vr)

def BRAR(OPEN, CLOSE, HIGH, LOW, N=26):     # 人气意愿指标
    """人气意愿指标"""
    ar = SUM(HIGH - OPEN, N) / SUM(OPEN - LOW, N) * 100
    br = SUM(MAX(0, HIGH - REF(CLOSE, 1)), N) / SUM(MAX(0, REF(CLOSE, 1) - LOW), N) * 100
    return RD(ar), RD(br)

def EMV(HIGH, LOW, VOLUME, N=14, M=9):      # 简易波动指标
    """Ease of Movement 简易波动指标"""
    mid = (HIGH + LOW) / 2
    diff = mid - REF(mid, 1)
    
    # 避免除零
    vol_ratio = np.where(HIGH - LOW != 0, VOLUME / (HIGH - LOW), 0)
    emv = diff / vol_ratio * 100000000
    maemv = MA(emv, M)
    
    return RD(emv), RD(maemv)

def ROC(CLOSE, N=12, M=6):                  # 变动率
    """Rate of Change 变动率"""
    roc = (CLOSE - REF(CLOSE, N)) / REF(CLOSE, N) * 100
    maroc = MA(roc, M)
    return RD(roc), RD(maroc)

def MTM(CLOSE, N=12, M=6):                  # 动量指标
    """Momentum 动量指标"""
    mtm = CLOSE - REF(CLOSE, N)
    mtmma = MA(mtm, M)
    return RD(mtm), RD(mtmma)

def DPO(CLOSE, N=20, M=10, K=6):            # 区间振荡指标
    """Detrended Price Oscillator 区间振荡指标"""
    dpo = CLOSE - REF(MA(CLOSE, N), K)
    madpo = MA(dpo, M)
    return RD(dpo), RD(madpo)

def ATR(CLOSE, HIGH, LOW, N=14):            # 真实波动幅度
    """Average True Range 真实波动幅度"""
    tr1 = HIGH - LOW
    tr2 = ABS(HIGH - REF(CLOSE, 1))
    tr3 = ABS(REF(CLOSE, 1) - LOW)
    tr = MAX(MAX(tr1, tr2), tr3)
    atr = MA(tr, N)
    return RD(atr)

def BOLL(CLOSE, N=20, P=2):                 # 布林线
    """Bollinger Bands 布林线"""
    mid = MA(CLOSE, N)
    tmp = STD(CLOSE, N)
    upper = mid + P * tmp
    lower = mid - P * tmp
    return RD(upper), RD(mid), RD(lower)  

def WR(CLOSE, HIGH, LOW, N=10, N1=6):            #W&R 威廉指标
    WR = (HHV(HIGH, N) - CLOSE) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    WR1 = (HHV(HIGH, N1) - CLOSE) / (HHV(HIGH, N1) - LLV(LOW, N1)) * 100
    return RD(WR), RD(WR1)

def BIAS(CLOSE,L1=6, L2=12, L3=24):              # BIAS乖离率
    BIAS1 = (CLOSE - MA(CLOSE, L1)) / MA(CLOSE, L1) * 100
    BIAS2 = (CLOSE - MA(CLOSE, L2)) / MA(CLOSE, L2) * 100
    BIAS3 = (CLOSE - MA(CLOSE, L3)) / MA(CLOSE, L3) * 100
    return RD(BIAS1), RD(BIAS2), RD(BIAS3)

def BOLL(CLOSE,N=20, P=2):                       #BOLL指标，布林带    
    MID = MA(CLOSE, N); 
    UPPER = MID + STD(CLOSE, N) * P
    LOWER = MID - STD(CLOSE, N) * P
    return RD(UPPER), RD(MID), RD(LOWER)    

def PSY(CLOSE,N=12, M=6):  
    PSY=COUNT(CLOSE>REF(CLOSE,1),N)/N*100
    PSYMA=MA(PSY,M)
    return RD(PSY),RD(PSYMA)

def CCI(CLOSE,HIGH,LOW,N=14):  
    TP=(HIGH+LOW+CLOSE)/3
    return (TP-MA(TP,N))/(0.015*AVEDEV(TP,N))
        
def ATR(CLOSE,HIGH,LOW, N=20):                    #真实波动N日平均值
    TR = MAX(MAX((HIGH - LOW), ABS(REF(CLOSE, 1) - HIGH)), ABS(REF(CLOSE, 1) - LOW))
    return MA(TR, N)

def BBI(CLOSE,M1=3,M2=6,M3=12,M4=20):             #BBI多空指标   
    return (MA(CLOSE,M1)+MA(CLOSE,M2)+MA(CLOSE,M3)+MA(CLOSE,M4))/4    

def DMI(CLOSE,HIGH,LOW,M1=14,M2=6):               #动向指标：结果和同花顺，通达信完全一致
    TR = SUM(MAX(MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1))), ABS(LOW - REF(CLOSE, 1))), M1)
    HD = HIGH - REF(HIGH, 1);     LD = REF(LOW, 1) - LOW
    DMP = SUM(IF((HD > 0) & (HD > LD), HD, 0), M1)
    DMM = SUM(IF((LD > 0) & (LD > HD), LD, 0), M1)
    PDI = DMP * 100 / TR;         MDI = DMM * 100 / TR
    ADX = MA(ABS(MDI - PDI) / (PDI + MDI) * 100, M2)
    ADXR = (ADX + REF(ADX, M2)) / 2
    return PDI, MDI, ADX, ADXR  

def TAQ(HIGH,LOW,N):                              #唐安奇通道交易指标，大道至简，能穿越牛熊
    UP=HHV(HIGH,N);    DOWN=LLV(LOW,N);    MID=(UP+DOWN)/2
    return UP,MID,DOWN

def TRIX(CLOSE,M1=12, M2=20):                      #三重指数平滑平均线
    TR = EMA(EMA(EMA(CLOSE, M1), M1), M1)
    TRIX = (TR - REF(TR, 1)) / REF(TR, 1) * 100
    TRMA = MA(TRIX, M2)
    return TRIX, TRMA

def VR(CLOSE,VOL,M1=26):                           #VR容量比率
    LC = REF(CLOSE, 1)
    return SUM(IF(CLOSE > LC, VOL, 0), M1) / SUM(IF(CLOSE <= LC, VOL, 0), M1) * 100

def EMV(HIGH,LOW,VOL,N=14,M=9):                     #简易波动指标 
    VOLUME=MA(VOL,N)/VOL;       MID=100*(HIGH+LOW-REF(HIGH+LOW,1))/(HIGH+LOW)
    EMV=MA(MID*VOLUME*(HIGH-LOW)/MA(HIGH-LOW,N),N);    MAEMV=MA(EMV,M)
    return EMV,MAEMV


def DPO(CLOSE,M1=20, M2=10, M3=6):                  #区间震荡线
    DPO = CLOSE - REF(MA(CLOSE, M1), M2);    MADPO = MA(DPO, M3)
    return DPO, MADPO

def BRAR(OPEN,CLOSE,HIGH,LOW,M1=26):                 #BRAR-ARBR 情绪指标  
    AR = SUM(HIGH - OPEN, M1) / SUM(OPEN - LOW, M1) * 100
    BR = SUM(MAX(0, HIGH - REF(CLOSE, 1)), M1) / SUM(MAX(0, REF(CLOSE, 1) - LOW), M1) * 100
    return AR, BR

def DMA(CLOSE,N1=10,N2=50,M=10):                     #平行线差指标  
    DIF=MA(CLOSE,N1)-MA(CLOSE,N2);    DIFMA=MA(DIF,M)
    return DIF,DIFMA

def MTM(CLOSE,N=12,M=6):                             #动量指标
    MTM=CLOSE-REF(CLOSE,N);         MTMMA=MA(MTM,M)
    return MTM,MTMMA

def ROC(CLOSE,N=12,M=6):                             #变动率指标
    ROC=100*(CLOSE-REF(CLOSE,N))/REF(CLOSE,N);    MAROC=MA(ROC,M)
    return ROC,MAROC  
  
  #望大家能提交更多指标和函数  https://github.com/mpquant/MyTT
