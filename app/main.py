import asyncio
import time
from math import ceil

from fastapi import FastAPI,Form
from pydantic import BaseModel
import uvicorn as u
from sqlalchemy import create_engine
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from joblib import Parallel, delayed
import re
from concurrent.futures import ThreadPoolExecutor
from starlette.responses import FileResponse


app = FastAPI(
    title='感染性事件计算工具',
    description= "感染性事件计算工具接口数据类型描述",
    version='1.0.0'
)
executor=ThreadPoolExecutor()

# 静态文件的挂载
app.mount("/static", StaticFiles(directory=r"D:\My_Pycharm\fastapi\static"), name="static")

templates = Jinja2Templates(directory=r"D:\My_Pycharm\fastapi\templates")


class Param(BaseModel):
    dbname : str
    dbdriver : str
    dbhost : str
    dbport : str
    dbuser : str
    dbpasswd : str
    dborcl : str
    cbasics : str
    antis : str
    opers : str
    temps : str
    bars : str
    departments : str
    allantinames : str
    begintime : str
    endtime : str
    process : str
    # is_oracle : str = '1'



def bg_compute(btime, etime, csv_name_手术患者明细, csv_name_非手术患者明细, csv_name, param, antis_dict):

    print("开始执⾏,进程号为%d,开始时间为%s" % (os.getpid(), pd.datetime.now()))
    time1=time.time()
    min_time = pd.to_datetime('1680-01-01')
    now_time = pd.datetime.now()

    engine = create_engine(param.dbname + "+" + param.dbdriver + "://" + param.dbuser + ":" + param.dbpasswd + "@" + param.dbhost + ":" + param.dbport + "/" + param.dborcl, echo=False,
        encoding='UTF-8')

    try:
        antis_权重 = pd.read_csv(r'../抗菌药物权重.csv')
    except:
        antis_权重 = pd.read_csv(r'../抗菌药物权重.csv', encoding='gbk')


    antis_权重 = antis_权重[['抗菌药物', '权重']]
    antis_权重.columns = ['aname', '权重']
    antis_权重.index = antis_权重['aname']
    antis_权重.index.name = 'cname'

    # 术前高等级用药和术后48小时高等级用药字典
    oper_高等级抗菌药物1 = pd.DataFrame(
        ['比阿培南', '厄他培南', '美罗培南', '帕尼培南倍他米隆', '法罗培南', '亚胺培南西司他丁', '头孢曲松钠舒巴坦', '头孢曲松钠他唑巴坦', '头孢噻肟舒巴坦', '头孢哌酮钠舒巴坦',
         '头孢哌酮他唑巴坦',
         '头孢他啶他唑巴坦', '依替米星', '异帕米星', '多西环素', '米诺环素', '替加环素', '替考拉宁', '万古霉素', '去甲万古霉素', '利奈唑胺', '泊沙康唑', '阿莫罗芬', '布替萘芬',
         '大蒜素', '伏康唑', '氟胞嘧啶', '氟康唑',
         '卡泊芬净', '克霉唑', '利福霉素', '联苯苄唑', '两性霉素B', '咪康唑', '米卡芬净', '那他霉素', '曲安奈德益康唑', '特比萘芬', '酮康唑', '伊曲康唑'],
        columns=['高等级抗菌药物1'])
    oper_高等级抗菌药物1['是否高等级用药1'] = 1
    oper_高等级抗菌药物1 = oper_高等级抗菌药物1.set_index(['高等级抗菌药物1'])

    oper_高等级抗菌药物2 = pd.DataFrame(
        ['比阿培南', '厄他培南', '美罗培南', '帕尼培南倍他米隆', '法罗培南', '亚胺培南西司他丁', '多西环素', '米诺环素', '替加环素', '替考拉宁', '万古霉素', '去甲万古霉素',
         '利奈唑胺',
         '泊沙康唑', '阿莫罗芬', '布替萘芬', '大蒜素', '伏康唑', '氟胞嘧啶', '氟康唑', '卡泊芬净', '克霉唑', '利福霉素', '联苯苄唑', '两性霉素B', '咪康唑', '米卡芬净',
         '那他霉素',
         '曲安奈德益康唑', '特比萘芬', '酮康唑', '伊曲康唑'], columns=['高等级抗菌药物2'])
    oper_高等级抗菌药物2['是否高等级用药2'] = 1
    oper_高等级抗菌药物2 = oper_高等级抗菌药物2.set_index(['高等级抗菌药物2'])

    # 统计时间段数据读取
    cbasic = pd.read_sql_query(param.cbasics, params=(btime, etime),con=engine)
    print(cbasic)
    departments = pd.read_sql_query(param.departments,params=(btime, etime), con=engine)
    print(departments)
    antis = pd.read_sql(param.antis, params=(btime, etime), con=engine)
    print(antis)
    opers = pd.read_sql(param.opers, params=(btime, etime), con=engine)
    print(opers)
    bars = pd.read_sql(param.bars, params=(btime, etime), con=engine)
    print(bars)
    temps = pd.read_sql(param.temps, params=(btime, etime), con=engine)
    print(temps)

    antis_抗真菌 = ['布替萘芬', '大蒜素', '伏康唑', '氟胞嘧啶', '氟康唑', '卡泊芬净', '克霉唑', '联苯苄唑', '两性霉素B',
                 '咪康唑', '米卡芬净', '那他霉素', '曲安奈德益康唑', '特比萘芬', '酮康唑', '伊曲康唑', '制霉菌素']

    if cbasic.shape[0] == 0 or departments.shape[0] == 0:
        pd.DataFrame(['本月住院患者信息或本月adt信息为空']).to_csv(csv_name[0:csv_name.rindex('/')] + 'ERROR.csv')
        print(btime + '-' + etime + "计算报错，文件路径为：" + csv_name[0:-9] + 'ERROR.csv')
        return 0

    # 住院每一天拆分
    def daily_days(x):
        try:
            dat = pd.date_range(x.入科时间[0:10], x.出科时间[0:10])
        except:
            dat = pd.date_range(x.入科时间[0:10], str(now_time)[0:10])
        dat = dat.astype(str)
        return str(list(dat.values)).replace('[', '').replace(']', '').replace('\'', '').replace(' ', '')

    departments['住院日期'] = departments.apply(lambda x: daily_days(x), axis=1)

    departments = departments.drop('住院日期', axis=1).join(
        departments['住院日期'].str.split(',', expand=True).stack().reset_index(level=1, drop=True).rename('住院日期'))
    departments['科室'] = departments['科室'].astype(str)

    # 合并每日科室
    def ab(df):
        return ','.join(df.values)

    datas = pd.DataFrame(departments.groupby(['caseid', '住院日期'])['科室'].apply(ab))
    datas = datas.reset_index()
    datas['住院日期'] = pd.to_datetime(datas['住院日期'])

    # 关联权重
    antis = antis.merge(antis_dict, on='抗菌药物')
    antis = antis[~antis['抗菌药物通用名'].isnull()].reset_index(drop=True)
    antis = antis.merge(antis_权重, left_on='抗菌药物通用名', right_on='aname', how='left')

    # 挑选出手术中用药，术中用药，药品使用时间为手术时间
    antis_手术用药 = antis[antis.apply(lambda x: False if pd.isnull(x.给药方式) else '术' in x.给药方式, axis=1)]
    antis_非手术用药 = antis.append(antis_手术用药).drop_duplicates(keep=False)

    # 修正手术用药时间
    if antis_手术用药.shape[0] > 0:
        antis_手术用药 = antis_手术用药.merge(opers, on='caseid', how='left')
        antis_手术用药 = antis_手术用药[antis_手术用药.手术开始时间 > antis_手术用药.医嘱开始时间]

        antis_手术用药 = antis_手术用药[['caseid', '抗菌药物通用名', '医嘱开始时间', '医嘱结束时间', '给药方式', 'aname', '权重', '手术开始时间']].groupby(
            ['caseid', '抗菌药物通用名', '医嘱开始时间', '医嘱结束时间', '给药方式', 'aname', '权重'])[['手术开始时间']].min()
        antis_手术用药 = antis_手术用药.reset_index()
        antis_手术用药['医嘱开始时间'] = antis_手术用药['手术开始时间']
        antis_手术用药.drop(columns=['手术开始时间'], inplace=True)

        # 修正手术用药结束时间
        def end_time(x):
            return x.医嘱开始时间 if x.医嘱开始时间 > x.医嘱结束时间 else x.医嘱结束时间

        antis_手术用药['医嘱结束时间'] = antis_手术用药[['医嘱开始时间', '医嘱结束时间']].apply(end_time, axis=1)
        antis = antis_非手术用药.append(antis_手术用药).reset_index(drop=True)

    # 对抗真菌药物做处理
    def is_fungi(x):
        return x.医嘱开始时间 if x.抗菌药物通用名 in antis_抗真菌 else x.医嘱结束时间

    # 处理抗真菌药物结束时间，由于抗真菌药物在处理升降级时只判断药物使用第一天
    antis['医嘱结束时间'] = antis[['医嘱开始时间', '医嘱结束时间', '抗菌药物通用名']].apply(is_fungi, axis=1)

    # 管理术前高等级抗菌药物
    antis = antis.merge(oper_高等级抗菌药物1, left_on='抗菌药物通用名', right_on='高等级抗菌药物1', how='left')
    # 关联术后48小时抗菌药物
    antis = antis.merge(oper_高等级抗菌药物2, left_on='抗菌药物通用名', right_on='高等级抗菌药物2', how='left')
    antis['医嘱开始时间'] = pd.to_datetime(antis['医嘱开始时间'])
    antis['医嘱结束时间'] = pd.to_datetime(antis['医嘱结束时间'])

    # 每日新开医嘱

    antis_每日新开医嘱 = antis[['caseid', '医嘱开始时间']]
    antis_每日新开医嘱['住院日期'] = antis_每日新开医嘱['医嘱开始时间'].map(lambda x: x.date())
    antis_每日新开医嘱['住院日期'] = pd.to_datetime(antis_每日新开医嘱['住院日期'])

    # 医嘱按日期展开
    # 耗时较长
    def daily_anti(x):
        dat = pd.date_range(x.医嘱开始时间.date(), x.医嘱结束时间.date())
        dat = dat.astype(str)
        return str(list(dat.values)).replace('[', '').replace(']', '').replace('\'', '').replace(' ', '')

    # 抗菌药物实际使用日
    antis['住院日期'] = antis.apply(lambda x: daily_anti(x), axis=1)
    # 抗菌药物日期展开
    antis = antis.drop('住院日期', axis=1).join(
        antis['住院日期'].str.split(',', expand=True).stack().reset_index(level=1, drop=True).rename('住院日期'))
    antis['住院日期'] = pd.to_datetime(antis['住院日期'])

    # 每日抗菌药物医嘱
    def abc(df):
        return str(sorted(df.values)).replace('[', '').replace(']', '').replace('\'', '')

    antis_每日抗菌药物 = antis[['caseid', '住院日期', '抗菌药物通用名']].drop_duplicates().groupby(['caseid', '住院日期'])['抗菌药物通用名'].apply(
        abc)
    antis_每日抗菌药物 = antis_每日抗菌药物.reset_index()
    datas = datas.merge(antis_每日抗菌药物, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')

    # 每日抗菌药物种类数量和权重统计
    # 耗时较长
    def daily_anti_sum(y):
        if y.抗菌药物通用名 is np.nan:
            return 0
        else:
            sum = 0
            s = y.抗菌药物通用名.split(',')
            for i in s:
                i = i.replace(' ', '')
                if i in antis_权重.index:
                    sum = sum + antis_权重['权重'].loc[i]
            return sum

    datas['抗菌药物种类数'] = datas.apply(lambda x: 0 if x.抗菌药物通用名 is np.nan else len(x.抗菌药物通用名.split(',')), axis=1)
    datas['抗菌药物权重和'] = datas.apply(daily_anti_sum, axis=1)

    # 前一天和后一天抗菌药物使用情况

    datas_前一天 = datas[['caseid', '住院日期', '抗菌药物通用名', '抗菌药物种类数', '抗菌药物权重和']]
    datas_前一天.columns = ['caseid', '住院日期', '前一天抗菌药物', '前一天抗菌药物种类数', '前一天抗菌药物权重和']
    datas_前一天['住院日期'] = datas_前一天['住院日期'].map(lambda x: x + timedelta(days=1))
    datas_前一天

    datas_后一天 = datas[['caseid', '住院日期', '抗菌药物通用名', '抗菌药物种类数', '抗菌药物权重和']]
    datas_后一天.columns = ['caseid', '住院日期', '后一天抗菌药物', '后一天抗菌药物种类数', '后一天抗菌药物权重和']
    datas_后一天['住院日期'] = datas_后一天['住院日期'].map(lambda x: x - timedelta(days=1))

    # 合并前一天后一天抗菌药物使用明细
    datas = datas.merge(datas_前一天, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')
    datas = datas.merge(datas_后一天, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')

    # 数据标化和数据类型标化
    datas['是否换药'] = '否'
    datas['是否升级'] = '否'
    datas['抗菌药物通用名'] = datas['抗菌药物通用名'].replace(np.nan, '')
    datas['前一天抗菌药物'] = datas['前一天抗菌药物'].replace(np.nan, '')
    datas['前一天抗菌药物种类数'] = datas['前一天抗菌药物种类数'].replace(np.nan, -1).astype('i8')
    datas['前一天抗菌药物权重和'] = datas['前一天抗菌药物权重和'].replace(np.nan, -1).astype('i8')
    datas['后一天抗菌药物'] = datas['后一天抗菌药物'].replace(np.nan, '')
    datas['后一天抗菌药物种类数'] = datas['后一天抗菌药物种类数'].replace(np.nan, -1).astype('i8')
    datas['后一天抗菌药物权重和'] = datas['后一天抗菌药物权重和'].replace(np.nan, -1).astype('i8')
    datas['抗菌药物前今后'] = datas.apply(lambda x: '是' if set(x.抗菌药物通用名) == set(x.前一天抗菌药物 + x.后一天抗菌药物) else '否', axis=1)

    # dataframe转numpy，并处理条件数组
    ndatas = datas.values
    cond_是否为第一天 = ndatas[:, -7] == -1
    cond_是否为非第一天和最后一天 = (ndatas[:, -7] != -1) & (ndatas[:, -5] != -1)
    cond_当天用药不同前一天 = ndatas[:, 3] != ndatas[:, 6]
    cond_前一天未用药 = ndatas[:, 6] == ''
    cond_当一天未用药 = ndatas[:, 3] == ''
    cond_后一天未用药 = ndatas[:, -6] == ''
    cond_当天权重大于前一天 = (ndatas[:, 4] > ndatas[:, 7]) | (ndatas[:, 5] > ndatas[:, 8])
    cond_当天药物等于前后两天 = ndatas[:, -1] == '是'
    cond_后一天权重大于前一天 = (ndatas[:, -5] > ndatas[:, 7]) | (ndatas[:, -4] > ndatas[:, 8])

    # 当日是否换药和抗菌药物升降级处理
    ndatas[:, [-3, -2]] = np.where(cond_是否为第一天[:, None],
                                   ['否', '否'],
                                   np.where(cond_是否为非第一天和最后一天[:, None],
                                            np.where(cond_当天用药不同前一天[:, None],
                                                     np.where(cond_前一天未用药[:, None],
                                                              ['否', '是'],
                                                              np.where(cond_当一天未用药[:, None],
                                                                       ['否', '否'],
                                                                       np.where(cond_后一天未用药[:, None],
                                                                                np.where(cond_当天权重大于前一天[:, None],
                                                                                         ['否', '是'],
                                                                                         ['否', '否']
                                                                                         ),
                                                                                np.where(cond_当天药物等于前后两天[:, None],
                                                                                         np.where(
                                                                                             cond_后一天权重大于前一天[:, None],
                                                                                             ['是', '是'],
                                                                                             ['是', '否']
                                                                                         ),
                                                                                         np.where(
                                                                                             cond_当天权重大于前一天[:, None],
                                                                                             ['否', '是'],
                                                                                             ['否', '否']
                                                                                         )
                                                                                         )
                                                                                )
                                                                       )
                                                              ),
                                                     ['否', '否']
                                                     ),
                                            np.where(cond_当天权重大于前一天[:, None],
                                                     ['否', '是'],
                                                     ['否', '否']
                                                     )
                                            )
                                   )

    # 根据前一天是否换药对抗菌药物升降级做修正
    datas = pd.DataFrame(ndatas, columns=datas.columns)
    datas
    datas_前一天是否换药 = datas[['caseid', '是否换药', '住院日期']]
    datas_前一天是否换药.columns = ['caseid', '前一天是否换药', '住院日期']
    datas_前一天是否换药['住院日期'] = datas_前一天是否换药['住院日期'].map(lambda x: x + timedelta(days=1))
    # datas_前一天是否换药

    datas = datas.merge(datas_前一天是否换药, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')
    datas['是否升级'] = datas.apply(lambda x: '否' if x.是否升级 == '是' and x.前一天是否换药 == '是' else x.是否升级, axis=1)

    # 每日最高体温
    temps['住院日期'] = temps['测量时间'].map(lambda x: x[0:10])
    temps_每日最高体温 = pd.DataFrame(temps[['caseid', '住院日期', '体温']].groupby(['caseid', '住院日期'])['体温'].max())
    temps_每日最高体温 = temps_每日最高体温.reset_index()
    temps_每日最高体温['住院日期'] = pd.to_datetime(temps_每日最高体温['住院日期'])
    datas = datas.merge(temps_每日最高体温, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')

    # 每日菌检出处理
    bars['住院日期'] = bars['检出时间'].map(lambda x: x[0:10])
    bars_每日菌检出 = bars[['caseid', '住院日期', '菌检出']].groupby(['caseid', '住院日期'])['菌检出'].apply(ab)
    bars_每日菌检出 = pd.DataFrame(bars_每日菌检出)
    bars_每日菌检出 = bars_每日菌检出.reset_index()
    bars_每日菌检出['住院日期'] = pd.to_datetime(bars_每日菌检出['住院日期'])
    datas = datas.merge(bars_每日菌检出, left_on=['caseid', '住院日期'], right_on=['caseid', '住院日期'], how='left')

    datas = datas.merge(cbasic, on='caseid')
    datas['入院时间'] = pd.to_datetime(datas['入院时间'])
    datas['出院时间'] = pd.to_datetime(datas['出院时间'])

    # 手术明细处理
    opers = opers[opers['手术开始时间'] != '0001-01-01 00:00:00'].reset_index(drop=True)
    opers_手术次数 = pd.DataFrame(opers.groupby(['caseid'])['手术开始时间'].count())

    opers_多台手术患者 = opers_手术次数[opers_手术次数['手术开始时间'] > 1].reset_index()

    opers_多台手术患者_手术信息 = opers[opers['caseid'].isin(opers_多台手术患者['caseid'])].reset_index(drop=True)
    opers_单台手术患者_手术信息 = opers[~opers['caseid'].isin(opers_多台手术患者['caseid'])].reset_index(drop=True)

    opers_多台手术患者_手术信息.手术开始时间 = pd.to_datetime(opers_多台手术患者_手术信息['手术开始时间'])
    opers_多台手术患者_手术信息.手术结束时间 = pd.to_datetime(opers_多台手术患者_手术信息['手术结束时间'])
    opers_多台手术患者_手术信息['下一次手术时间'] = now_time

    if opers_多台手术患者_手术信息.shape[0] > 0:
        # 多台手术患者，手术结转
        opers_结转_lis1 = []
        opers_结转_lis2 = []
        opers_结转_lis3 = []
        opers_结转_lis4 = []
        opers_结转_lis5 = []

        ind = opers_多台手术患者_手术信息.loc[0]

        for i, r in opers_多台手术患者_手术信息.iterrows():
            if i == 0:
                continue
            if r.caseid == ind.caseid:
                if ind.手术结束时间 + timedelta(days=2) >= r.手术开始时间:
                    ind.手术结束时间 = r.手术开始时间
                    ind.手术名称 = ind.手术名称 + ',' + r.手术名称
                else:
                    ind.下一次手术时间 = r.手术开始时间
                    opers_结转_lis1.extend([ind['caseid']])
                    opers_结转_lis2.extend([ind['手术开始时间'].strftime('%Y-%m-%d %H:%M:%S')])
                    opers_结转_lis3.extend([ind['手术名称']])
                    opers_结转_lis4.extend([ind['手术结束时间'].strftime('%Y-%m-%d %H:%M:%S')])
                    opers_结转_lis5.extend([ind['下一次手术时间'].strftime('%Y-%m-%d %H:%M:%S')])
                    # opers_结转=opers_结转.append(ind)
                    ind = r
            else:
                opers_结转_lis1.extend([ind['caseid']])
                opers_结转_lis2.extend([ind['手术开始时间'].strftime('%Y-%m-%d %H:%M:%S')])
                opers_结转_lis3.extend([ind['手术名称']])
                opers_结转_lis4.extend([ind['手术结束时间'].strftime('%Y-%m-%d %H:%M:%S')])
                opers_结转_lis5.extend([ind['下一次手术时间'].strftime('%Y-%m-%d %H:%M:%S')])
                # opers_结转=opers_结转.append(ind)
                ind = r

        opers_结转 = pd.DataFrame(
            {'caseid': opers_结转_lis1, '手术开始时间': opers_结转_lis2, '手术名称': opers_结转_lis3, '手术结束时间': opers_结转_lis4,
             '下一次手术时间': opers_结转_lis5})
        opers_结转 = opers_结转.drop_duplicates().reset_index(drop=True)
    else:
        opers_结转 = pd.DataFrame(columns=['caseid', '手术开始时间', '手术名称', '手术结束时间', '下一次手术时间'])
    opers_单台手术患者_手术信息['下一次手术'] = now_time

    # 合并单台手术信息和多台手术结转后的手术信息
    if opers_结转.shape[0] > 0:
        opers_合并 = opers_结转.append(opers_单台手术患者_手术信息)
        opers_合并 = opers_合并.reset_index(drop=True)
    else:
        opers_合并 = opers_单台手术患者_手术信息

    opers_合并['手术开始时间'] = pd.to_datetime(opers_合并['手术开始时间'])
    opers_合并['手术结束时间'] = pd.to_datetime(opers_合并['手术结束时间'])
    opers_合并['下一次手术'] = pd.to_datetime(opers_合并['下一次手术'])

    opers_合并['手术前一天'] = opers_合并['手术开始时间'].map(lambda x: x - timedelta(days=1))
    opers_合并['手术后两天'] = opers_合并['手术结束时间'].map(lambda x: x + timedelta(days=2))
    opers_合并['下台手术前一天'] = opers_合并['下一次手术'].map(lambda x: x - timedelta(days=1))

    antis['住院日期'] = antis['住院日期'].map(lambda x: x.date())
    antis['住院日期'] = pd.to_datetime(antis['住院日期'])

    antis_高等级用药医嘱 = antis[['caseid', '抗菌药物通用名', '医嘱开始时间', '医嘱结束时间', '是否高等级用药1', '是否高等级用药2']].drop_duplicates()

    antis_高等级用药医嘱 = antis_高等级用药医嘱[(antis_高等级用药医嘱.是否高等级用药1 == 1) | (antis_高等级用药医嘱.是否高等级用药2 == 1)].reset_index(drop=True)

    opers_高等级用药合并 = opers_合并.merge(antis_高等级用药医嘱, on='caseid', how='left')

    opers_高等级用药合并['术前一天使用高等级药物'] = np.where(
        (opers_高等级用药合并['是否高等级用药1'] == 1) & (opers_高等级用药合并['手术前一天'] <= opers_高等级用药合并['医嘱结束时间']) & (
                opers_高等级用药合并['手术开始时间'] > opers_高等级用药合并['医嘱开始时间']), 1, 0)
    opers_高等级用药合并['术后两天使用高等级药物'] = np.where(
        (opers_高等级用药合并['是否高等级用药2'] == 1) & (opers_高等级用药合并['手术后两天'] < opers_高等级用药合并['医嘱结束时间']) & (
                opers_高等级用药合并['下台手术前一天'] >= opers_高等级用药合并['医嘱开始时间']), 1, 0)
    opers_高等级用药合并 = opers_高等级用药合并[
        ['caseid', '手术开始时间', '手术名称', '手术结束时间', '下一次手术', '手术前一天', '手术后两天', '下台手术前一天', '术前一天使用高等级药物',
         '术后两天使用高等级药物']].groupby(['caseid', '手术开始时间', '手术名称', '手术结束时间', '下一次手术', '手术前一天', '手术后两天', '下台手术前一天'])[
        ['术前一天使用高等级药物', '术后两天使用高等级药物']].sum()
    opers_高等级用药合并 = opers_高等级用药合并.reset_index()

    temps['测量时间'] = pd.to_datetime(temps['测量时间'])
    temps['住院日期'] = pd.to_datetime(temps['住院日期'])
    temps = temps.groupby(['caseid', '住院日期'])[['测量时间']].max().merge(
        temps.groupby(['caseid', '住院日期'])[['测量时间']].min().reset_index(), on=['caseid', '住院日期'])
    temps.rename(columns={'测量时间_x': '当日最小体温大于38度时间', '测量时间_y': '当日最大体温大于38度时间'}, inplace=True)

    opers_高等级用药体温合并 = opers_高等级用药合并.merge(temps, left_on=['caseid'], right_on=['caseid'], how='left')
    opers_高等级用药体温合并['术后两天体温是否大于38'] = np.where(
        (opers_高等级用药体温合并['住院日期'] is not np.nan) & (opers_高等级用药体温合并['手术后两天'] < opers_高等级用药体温合并['当日最大体温大于38度时间']) & (
                opers_高等级用药体温合并['下台手术前一天'] >= opers_高等级用药体温合并['当日最小体温大于38度时间']), 1, 0)
    opers_高等级用药体温合并 = opers_高等级用药体温合并.groupby(
        ['caseid', '手术开始时间', '手术名称', '手术结束时间', '下一次手术', '手术前一天', '手术后两天', '下台手术前一天', '术前一天使用高等级药物', '术后两天使用高等级药物'])[
        ['术后两天体温是否大于38']].sum()
    opers_高等级用药体温合并 = opers_高等级用药体温合并.reset_index()

    antis_每日新开医嘱 = antis_每日新开医嘱.groupby(['caseid', '住院日期'])[['医嘱开始时间']].max().merge(
        antis_每日新开医嘱.groupby(['caseid', '住院日期'])[['医嘱开始时间']].min().reset_index(), on=['caseid', '住院日期'])

    antis_每日新开医嘱.rename(columns={'医嘱开始时间_x': '当日最小新开医嘱时间', '医嘱开始时间_y': '当日最大新开医嘱时间'}, inplace=True)

    opers_高等级用药体温合并['手术后两天日期'] = opers_高等级用药体温合并['手术后两天'].map(lambda x: x.date())
    opers_高等级用药体温合并['手术后两天日期'] = pd.to_datetime(opers_高等级用药体温合并['手术后两天日期'])
    opers_高等级用药体温合并['下台手术前一天日期'] = opers_高等级用药体温合并['下台手术前一天'].map(lambda x: x.date())
    opers_高等级用药体温合并['下台手术前一天日期'] = pd.to_datetime(opers_高等级用药体温合并['下台手术前一天日期'])

    antis_每日新开医嘱['住院日期'] = antis_每日新开医嘱['住院日期'].apply(lambda x: x.date())
    antis_每日新开医嘱['住院日期'] = pd.to_datetime(antis_每日新开医嘱['住院日期'])

    opers_高等级用药体温新开医嘱合并 = opers_高等级用药体温合并.merge(antis_每日新开医嘱, left_on=['caseid', '手术后两天日期'],
                                                right_on=['caseid', '住院日期'], how='left')
    opers_高等级用药体温新开医嘱合并.rename(columns={'当日最小新开医嘱时间': '术后48h最小新开医嘱时间', '当日最大新开医嘱时间': '术后48h最大新开医嘱时间'}, inplace=True)

    opers_高等级用药体温新开医嘱合并 = opers_高等级用药体温新开医嘱合并.merge(antis_每日新开医嘱, left_on=['caseid', '下台手术前一天日期'],
                                                    right_on=['caseid', '住院日期'], how='left')
    opers_高等级用药体温新开医嘱合并.rename(columns={'当日最小新开医嘱时间': '下台手术前一天最小新开医嘱时间', '当日最大新开医嘱时间': '下台手术前一天最大新开医嘱时间'}, inplace=True)

    opers_高等级用药体温新开医嘱合并.drop(columns=['住院日期_y', '住院日期_x'], inplace=True)

    opers11 = opers_高等级用药体温新开医嘱合并.merge(datas[['caseid', '住院日期', '是否升级']], on=['caseid'])

    opers11['下台手术前一天最小新开医嘱时间'] = opers11['下台手术前一天最小新开医嘱时间'].replace(np.nan, now_time)
    opers11['术后48h最大新开医嘱时间'] = opers11['术后48h最大新开医嘱时间'].replace(np.nan, min_time)
    opers11['术后48h最大新开医嘱时间'] = pd.to_datetime(opers11['术后48h最大新开医嘱时间'])
    opers11['下台手术前一天最小新开医嘱时间'] = pd.to_datetime(opers11['下台手术前一天最小新开医嘱时间'])

    opers11['术后第三天至下次手术前第二天是否抗菌药物升级'] = np.where(
        (opers11['手术后两天'] < opers11['住院日期']) & (opers11['下台手术前一天'] > opers11['住院日期']) & (opers11['是否升级'] == '是'), 1, 0)

    opers11['术后第二天是否抗菌药物升级'] = np.where(
        (opers11['手术后两天日期'] == opers11['住院日期']) & (opers11['术后48h最大新开医嘱时间'] > opers11['手术后两天']) & (
                opers11['是否升级'] == '是'), 1, 0)

    opers11['下次手术前一天是否抗菌药物升级'] = np.where(
        (opers11['下台手术前一天日期'] == opers11['住院日期']) & (opers11['下台手术前一天最小新开医嘱时间'] <= opers11['下台手术前一天']) & (
                opers11['是否升级'] == '是'), 1, 0)

    opers11['术后48小时是否存在抗菌药物升级'] = np.where(
        (opers11['术后第三天至下次手术前第二天是否抗菌药物升级'] == 1) | (opers11['术后第二天是否抗菌药物升级'] == 1) | (opers11['下次手术前一天是否抗菌药物升级'] == 1),
        1, 0)

    opers11 = opers11.groupby(
        ['caseid', '手术开始时间', '手术名称', '手术结束时间', '下一次手术', '手术前一天', '手术后两天', '下台手术前一天', '术前一天使用高等级药物', '术后两天使用高等级药物',
         '术后两天体温是否大于38'])[['术后48小时是否存在抗菌药物升级']].sum()
    opers11 = opers11.reset_index()

    oper_术前使用高等级药物 = opers11[opers11.术前一天使用高等级药物 > 0][['caseid']].drop_duplicates()
    oper_术前使用高等级药物['是否院内感染'] = '术前一天使用高等级药物'

    opers_术前未使用高等级药物 = opers11[~opers11.caseid.isin(oper_术前使用高等级药物)]
    opers_术前未使用高等级药物['是否院内感染'] = np.where(
        ((opers_术前未使用高等级药物['术后两天体温是否大于38'] > 0) & (opers_术前未使用高等级药物['术后48小时是否存在抗菌药物升级'] > 0)) | (
                (opers_术前未使用高等级药物['术后两天体温是否大于38'] == 0) & (opers_术前未使用高等级药物['术后两天使用高等级药物'] > 0)), 1, 0)

    opers_术前未使用高等级药物 = opers_术前未使用高等级药物[['caseid', '是否院内感染']].groupby(['caseid'])[['是否院内感染']].sum()
    opers_术前未使用高等级药物 = opers_术前未使用高等级药物.reset_index()
    opers_术前未使用高等级药物['是否院内感染'] = np.where(opers_术前未使用高等级药物['是否院内感染'] > 0, '院内感染', '非院内感染')

    opers11['住院日期'] = opers11['手术开始时间'].map(lambda x: x.date())

    opers11['住院日期'] = pd.to_datetime(opers11['住院日期'])
    datas_手术患者 = datas[(datas['caseid'].isin(opers_结转['caseid']) | datas['caseid'].isin(opers_单台手术患者_手术信息['caseid']))]

    datas_手术患者 = datas_手术患者.merge(opers11, on=['caseid', '住院日期'], how='left').reset_index(drop=True)

    print(csv_name_手术患者明细)
    datas_手术患者.to_csv(csv_name_手术患者明细, mode='a', index=False, header=True)

    datas['入院第三天'] = datas['入院时间'] + timedelta(days=2)
    temp_入院三天内是否存在体温38 = \
        datas[(datas['住院日期'] <= datas['入院第三天']) & (datas['体温'] >= 38)][['caseid']].drop_duplicates().groupby(
            ['caseid'])[
            ['caseid']].count()
    temp_入院三天内是否存在体温38.columns = ['入院三天内是否体温38']
    temp_入院三天内是否存在体温38 = temp_入院三天内是否存在体温38.reset_index()

    datas = datas.merge(temp_入院三天内是否存在体温38, on='caseid', how='left')
    datas['入院三天内是否体温38'] = datas['入院三天内是否体温38'].replace(np.nan, 0).astype('i8')

    temp_入院三天内是否使用抗菌药物 = \
        datas[(datas['住院日期'] <= datas['入院第三天']) & (datas['抗菌药物种类数'] > 0)][['caseid']].drop_duplicates().groupby(
            ['caseid'])[
            ['caseid']].count()
    temp_入院三天内是否使用抗菌药物.columns = ['入院三天内是否使用抗菌药物']
    temp_入院三天内是否使用抗菌药物 = temp_入院三天内是否使用抗菌药物.reset_index()

    datas = datas.merge(temp_入院三天内是否使用抗菌药物, on='caseid', how='left')
    datas['入院三天内是否使用抗菌药物'] = datas['入院三天内是否使用抗菌药物'].replace(np.nan, 0).astype('i8')

    datas['入院第十四天'] = datas['入院时间'] + timedelta(days=13)
    temp_入院十四天后是否存在体温38 = \
        datas[(datas['住院日期'] >= datas['入院第十四天']) & (datas['体温'] >= 38)][['caseid']].drop_duplicates().groupby(
            ['caseid'])[
            ['caseid']].count()
    temp_入院十四天后是否存在体温38.columns = ['入院十四天后是否体温38']
    temp_入院十四天后是否存在体温38 = temp_入院十四天后是否存在体温38.reset_index()

    datas = datas.merge(temp_入院十四天后是否存在体温38, on='caseid', how='left')
    datas['入院十四天后是否体温38'] = datas['入院十四天后是否体温38'].replace(np.nan, 0).astype('i8')

    temp_入院十四天后是否存在抗菌药物升级 = \
        datas[(datas['住院日期'] >= datas['入院第十四天']) & (datas['是否升级'] == '是')][['caseid']].drop_duplicates().groupby(
            ['caseid'])[['caseid']].count()
    temp_入院十四天后是否存在抗菌药物升级.columns = ['入院十四天后是否抗菌药物升级']
    temp_入院十四天后是否存在抗菌药物升级 = temp_入院十四天后是否存在抗菌药物升级.reset_index()

    datas = datas.merge(temp_入院十四天后是否存在抗菌药物升级, on='caseid', how='left')
    datas['入院十四天后是否抗菌药物升级'] = datas['入院十四天后是否抗菌药物升级'].replace(np.nan, 0).astype('i8')

    temp_入院三天后是否存在体温38 = \
        datas[(datas['住院日期'] >= datas['入院第三天']) & (datas['体温'] >= 38)][['caseid']].drop_duplicates().groupby(
            ['caseid'])[
            ['caseid']].count()
    temp_入院三天后是否存在体温38.columns = ['入院三天后是否存在体温38']
    temp_入院三天后是否存在体温38 = temp_入院三天后是否存在体温38.reset_index()

    datas = datas.merge(temp_入院三天后是否存在体温38, on='caseid', how='left')
    datas['入院三天后是否存在体温38'] = datas['入院三天后是否存在体温38'].replace(np.nan, 0).astype('i8')

    temp_入院三天后是否存在抗菌药物升级 = \
        datas[(datas['住院日期'] >= datas['入院第三天']) & (datas['是否升级'] == '是')][['caseid']].drop_duplicates().groupby(
            ['caseid'])[
            ['caseid']].count()
    temp_入院三天后是否存在抗菌药物升级.columns = ['入院三天后是否抗菌药物升级']
    temp_入院三天后是否存在抗菌药物升级 = temp_入院三天后是否存在抗菌药物升级.reset_index()

    datas = datas.merge(temp_入院三天后是否存在抗菌药物升级, on='caseid', how='left')
    datas['入院三天后是否抗菌药物升级'] = datas['入院三天后是否抗菌药物升级'].replace(np.nan, 0).astype('i8')

    datas_非手术患者 = datas[~(datas['caseid'].isin(opers_结转['caseid']) | datas['caseid'].isin(opers_单台手术患者_手术信息['caseid']))]

    datas_非手术患者.to_csv(csv_name_非手术患者明细, mode='a', index=False, header=True)

    n非手术datas = datas_非手术患者.values
    cond_入院三天内存在发热且使用抗菌药物 = (n非手术datas[:, -7] > 0) & (n非手术datas[:, -7] > 0)
    cond_入院十四天后存在发热且使用抗菌药物升级 = (n非手术datas[:, -4] > 0) & (n非手术datas[:, -3] > 0)
    cond_入院三天后存在发热且使用抗菌药物升级 = (n非手术datas[:, -2] > 0) & (n非手术datas[:, -1] > 0)
    np_result = np.where(cond_入院三天内存在发热且使用抗菌药物[:, None],
                         np.where(cond_入院十四天后存在发热且使用抗菌药物升级[:, None], 1, 0),
                         np.where(cond_入院三天后存在发热且使用抗菌药物升级[:, None], 1, 0)
                         )
    datas_非手术患者['是否院内感染'] = np_result

    opers_非手术患者 = datas_非手术患者[['caseid', '是否院内感染']].groupby(['caseid'])[['是否院内感染']].sum()
    opers_非手术患者 = opers_非手术患者.reset_index()
    opers_非手术患者['是否院内感染'] = np.where(opers_非手术患者['是否院内感染'] > 0, '院内感染', '非院内感染')
    opers_非手术患者['是否手术患者'] = '否'
    opers_术前未使用高等级药物['是否手术患者'] = '是'
    oper_术前使用高等级药物['是否手术患者'] = '是'

    oper_术前使用高等级药物 = oper_术前使用高等级药物[~oper_术前使用高等级药物['caseid'].isin(opers_术前未使用高等级药物['caseid'])]

    case感染性事件 = opers_非手术患者
    case感染性事件 = case感染性事件.append(opers_术前未使用高等级药物)
    case感染性事件 = case感染性事件.append(oper_术前使用高等级药物)
    case感染性事件 = case感染性事件.reset_index(drop=True)

    case感染性事件.to_csv(csv_name, index=False, header=True)
    time2 = time.time()
    print("结束执⾏,进程号为%d ,进程时长%.2f,结束时间为%s" % (os.getpid(), time2 - time1, pd.datetime.now()))

def list_months(btime,months):
    start_time = datetime.strptime(btime, '%Y-%m-%d %H:%M:%S')
    end_time = start_time + relativedelta(months=1) - relativedelta(seconds=1)
    bt = []
    et = []
    bt.append(btime)
    et.append(str(end_time))
    for i in range(1, months):
        bt.append(str(datetime.strptime(bt[-1], '%Y-%m-%d %H:%M:%S') + relativedelta(months=1)))
        et.append(
            str(datetime.strptime(bt[-1], '%Y-%m-%d %H:%M:%S') + relativedelta(months=1) - relativedelta(seconds=1)))
    return bt,et
def discriminated_antis(all_antis):
    try:
        df_抗菌药物 = pd.read_csv(r'../抗菌药物字典.csv')
    except:
        df_抗菌药物 = pd.read_csv(r'../抗菌药物字典.csv', encoding='gbk')
    def isanti(x):
        df_抗菌药物['药品'] = x.抗菌药物
        df1 = df_抗菌药物[df_抗菌药物['规则等级']==1]
        if x.抗菌药物 in list(df1['匹配规则'].values):
            return df1[df1['匹配规则']==x.抗菌药物].reset_index(drop=True).loc[0]['抗菌药物通用名']
        else:
            df2 = df_抗菌药物[df_抗菌药物['规则等级']==2]
            df2['是否匹配'] = df2.apply(lambda y: y.抗菌药物通用名 if re.match(y.匹配规则, y.药品) else np.nan, axis=1)
            df2['匹配长度'] = df2.apply(lambda y: 0 if pd.isnull(y.是否匹配) else len( y.匹配规则 ), axis=1)
            if df2[~df2['是否匹配'].isnull()].shape[0]==0:
                df3 = df_抗菌药物[df_抗菌药物['规则等级']==3]
                df3['是否匹配'] = df3.apply(lambda y: y.抗菌药物通用名 if re.match(y.匹配规则, y.药品) else np.nan, axis=1)
                df3['匹配长度'] = df3.apply(lambda y: 0 if pd.isnull(y.是否匹配) else len( y.匹配规则 ), axis=1)
                if df3[~df3['是否匹配'].isnull()].shape[0]==0:
                    df4 = df_抗菌药物[df_抗菌药物['规则等级']==4]
                    df4['是否匹配'] = df4.apply(lambda y: y.抗菌药物通用名 if re.match(y.匹配规则, y.药品) else np.nan, axis=1)
                    df4['匹配长度'] = df4.apply(lambda y: 0 if pd.isnull(y.是否匹配) else len( y.匹配规则 ), axis=1)
                    if df4[~df4['是否匹配'].isnull()].shape[0]==0:
                        return np.nan
                    else:
                        return df4[~df4['是否匹配'].isnull()][['抗菌药物通用名','匹配长度']].drop_duplicates().sort_values(by=['匹配长度'], ascending=False).reset_index(drop=True)['抗菌药物通用名'].loc[0]#返回正则匹配成功且匹配长度最长
                else:
                    return df3[~df3['是否匹配'].isnull()][['抗菌药物通用名','匹配长度']].drop_duplicates().sort_values(by=['匹配长度'], ascending=False).reset_index(drop=True)['抗菌药物通用名'].loc[0]#返回正则匹配成功且匹配长度最长
            else:
                return df2[~df2['是否匹配'].isnull()][['抗菌药物通用名','匹配长度']].drop_duplicates().sort_values(by=['匹配长度'], ascending=False).reset_index(drop=True)['抗菌药物通用名'].loc[0]#返回正则匹配成功且匹配长度最长
    all_antis['抗菌药物通用名'] = all_antis.apply(isanti, axis=1)
    return all_antis

# @app.post("/compute")
# def compute(dbname : str = Form(...),dbdriver : str = Form(...),dbhost : str = Form(...),dbport : str = Form(...),dbuser : str = Form(...),
#             dbpasswd : str = Form(...),dborcl : str = Form(...),cbasics : str = Form(...),antis : str = Form(...),opers : str = Form(...),
#             temps : str = Form(...),bars : str = Form(...),departments : str = Form(...),allantinames : str = Form(...),begintime : str = Form(...),
#             endtime : str = Form(...),process : str = Form(...)):
#
#     pp = {
#         "dbname": dbname,
#         "dbdriver": dbdriver,
#         "dbhost": dbhost,
#         "dbport": dbport,
#         "dbuser": dbuser,
#         "dbpasswd": dbpasswd,
#         "dborcl": dborcl,
#         "cbasics": cbasics.replace('\r\n',''),
#         "antis": antis.replace('\r\n',''),
#         "opers": opers.replace('\r\n',''),
#         "temps": temps.replace('\r\n',''),
#         "bars": bars.replace('\r\n',''),
#         "departments": departments.replace('\r\n',''),
#         "allantinames": allantinames.replace('\r\n',''),
#         "begintime": begintime,
#         "endtime": endtime,
#         "process": process,
#         "is_oracle": 1
#     }
#     param = Param(**pp)
#     print(param)

@app.post("/compute",tags=["感染性事件计算工具接口"],description="NIS数据源，感染性事件计算工具接口")
def compute(request : Request , dbname : str = Form(...),dbdriver : str = Form(...),dbhost : str = Form(...),dbport : str = Form(...),dbuser : str = Form(...),
            dbpasswd : str = Form(...),dborcl : str = Form(...),cbasics : str = Form(...),antis : str = Form(...),opers : str = Form(...),
            temps : str = Form(...),bars : str = Form(...),departments : str = Form(...),allantinames : str = Form(...),begintime : str = Form(...),
            endtime : str = Form(...),process : str = Form(...)):

    pp = {
        "dbname": dbname,
        "dbdriver": dbdriver,
        "dbhost": dbhost,
        "dbport": dbport,
        "dbuser": dbuser,
        "dbpasswd": dbpasswd,
        "dborcl": dborcl,
        "cbasics": cbasics.replace('\r\n',''),
        "antis": antis.replace('\r\n',''),
        "opers": opers.replace('\r\n',''),
        "temps": temps.replace('\r\n',''),
        "bars": bars.replace('\r\n',''),
        "departments": departments.replace('\r\n',''),
        "allantinames": allantinames.replace('\r\n',''),
        "begintime": begintime,
        "endtime": endtime,
        "process": process,
        "is_oracle": 1
    }
    param = Param(**pp)
    print(param)
    btime = param.begintime + " 00:00:00"
    etime = param.endtime + " 00:00:00"

    btimes, etimes = list_months(btime, ceil((pd.to_datetime(etime) - pd.to_datetime(btime)).days / 30))
    print(btimes, etimes)
    now_time = pd.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    csv_name_手术患者明细 = []
    csv_name_非手术患者明细 = []
    csv_name = []
    path = []
    for i in range(len(btimes)):
        path.extend(['./out/' + now_time + '-' + btimes[i][0:10] + "-" + etimes[i][0:10]])
        os.makedirs(path[-1])
        csv_name_手术患者明细.extend(
            [path[-1] + '/' + now_time + '-' + btimes[i][0:10] + "-" + etimes[i][0:10] + '手术患者明细.csv'])
        csv_name_非手术患者明细.extend(
            [path[-1] + '/' + now_time + '-' + btimes[i][0:10] + "-" + etimes[i][0:10] + '非手术患者明细.csv'])
        csv_name.extend([path[-1] + '/' + now_time + '-' + btimes[i][0:10] + "-" + etimes[i][0:10] + '感染性事件.csv'])
    engine = create_engine( param.dbname + "+" +  param.dbdriver + "://" +  param.dbuser + ":" +  param.dbpasswd  + "@" +  param.dbhost + ":" +  param.dbport + "/" +  param.dborcl , echo=False,encoding='UTF-8')
    print(engine)
    print( param.begintime ,  param.endtime , type( param.begintime ),type( param.endtime) ,btime ,etime)
    all_antis = pd.read_sql( param.allantinames, params=(btime, etime), con=engine)

    antis_dict = discriminated_antis(all_antis)
    antis_未被识别 = antis_dict[antis_dict['抗菌药物通用名'].isnull()][['抗菌药物']]
    if antis_未被识别.shape[0] > 0:
        # print("存在抗菌药物名称未识别！！！")
        print("存在抗菌药物名称未识别！！！文件地址：/out/抗菌药物未被识别/" + now_time + '-' + btime[0:10] + "-" + etime[0:10] + '抗菌药物未被识别.csv')
        if os.path.exists('./out/抗菌药物未被识别'):
            antis_未被识别.to_csv('./out/抗菌药物未被识别/' + now_time + '-' + btime[0:10] + "-" + etime[0:10] + '抗菌药物未被识别.csv',
                              index=False)
        else:
            os.makedirs('./out/抗菌药物未被识别')
            antis_未被识别.to_csv('./out/抗菌药物未被识别/' + now_time + '-' + btime[0:10] + "-" + etime[0:10] + '抗菌药物未被识别.csv',
                              index=False)

    try:
        Parallel(n_jobs=int( param.process), backend="multiprocessing")(
            delayed(bg_compute)(btimes[i], etimes[i], csv_name_手术患者明细[i], csv_name_非手术患者明细[i], csv_name[i], param, antis_dict)
            for i in
            range(len(btimes)))

        zipname = "./out/" + now_time + ".zip"
        f = zipfile.ZipFile(zipname, 'a', zipfile.ZIP_DEFLATED)

        for i1 in range(0,len(csv_name)):
            f.write(csv_name[i1], csv_name[i1].split('/')[-1])
            f.write(csv_name_手术患者明细[i1], csv_name_手术患者明细[i1].split('/')[-1])
            f.write(csv_name_非手术患者明细[i1], csv_name_非手术患者明细[i1].split('/')[-1])
        f.close()
        return FileResponse(zipname, filename=now_time + ".zip")

        # return templates.TemplateResponse('home.html', {"request": request, "data": {'message': '成功'}})
    except:
        return templates.TemplateResponse('home.html', {"request": request, "data": {'message': '失败'}})


async def ftest():
    time.sleep(10)
    print(111)

@app.get("/test/{index}")
def test(index : int ,request : Request):
    if index == 1:
        # await  asyncio.sleep(5)
        # time.sleep(5)
        # loop = asyncio.get_event_loop()
        # await loop.run_in_executor(None, ftest)
        # await asyncio.ftest()
        # return {"message:休眠5s"}
        return templates.TemplateResponse('home.html',{"request":request})
    elif index == 2:
        return templates.TemplateResponse('home1.html', {"request": request})
    elif index == 3:
        return templates.TemplateResponse('home2.html', {"request": request})
    else:
        return {"message:立即响应"}
import zipfile
@app.get("/test1/{index}")
def test1(index : int):
    f = zipfile.ZipFile('./out/2021-09-22-14-24-13-2019-01-01-2019-01-31.zip', 'a', zipfile.ZIP_DEFLATED)
    for file in os.listdir(r"D:\My_Pycharm\fastapi\app\out\2021-09-22-14-24-13-2019-01-01-2019-01-31"):
        f.write(r"D:\My_Pycharm\fastapi\app\out\2021-09-22-14-24-13-2019-01-01-2019-01-31"+"\\"+file,file)
    f.close()
    return FileResponse('./out/2021-09-22-14-24-13-2019-01-01-2019-01-31.zip', filename='2021-09-22-14-24-13-2019-01-01-2019-01-31.zip')


if __name__ == '__main__':
    u.run(app='main:app', host="10.0.68.84", port=5555,workers=10 ,reload=True)
#
# {
#   "dbname": "oracle",
#   "dbdriver": "cx_oracle",
#   "dbhost": "10.0.68.84",
#   "dbport": "1521",
#   "dbuser": "anis",
#   "dbpasswd": "nis5admin",
#   "dborcl": "orcl",
#   "cbasics": "select CASEID,IN_TIME as 入院时间,OUT_TIME as 出院时间 from overall where OUT_TIME>=:1 and IN_TIME<=:2",
#   "antis": "select CASEID,ANAME as 抗菌药物,BEGINTIME as 医嘱开始时间,ENDTIME as 医嘱结束时间,ADMINISTRATION as 给药方式 from ANTIBIOTICS where caseid in (select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) and substr(BEGINTIME,1,4)>'1900' and substr(BEGINTIME,1,4)<'2022' and substr(ENDTIME,1,4)>'1900' and substr(ENDTIME,1,4)<'2022' order by BEGINTIME",
#   "opers": "select CASEID,BEGINTIME as 手术开始时间,OPER_NAME as 手术名称, ENDTIME as 手术结束时间 from OPER2 where caseid in (select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) and substr(BEGINTIME,1,4)>'1900' and substr(BEGINTIME,1,4)<'2022' and substr(ENDTIME,1,4)>'1900' and substr(ENDTIME,1,4)<'2022' order by BEGINTIME",
#   "temps": "select CASEID,VALUE as 体温,RECORDDATE as 测量时间 from TEMPERATURE where caseid in (select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) order by RECORDDATE",
#   "bars": "select CASEID,BACTERIA as 菌检出,REPORTTIME as 检出时间 from BACTERIA where caseid in (select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) order by REPORTTIME",
#   "departments": "select t1.CASEID,t1.入科时间,t2.label as 科室,t1.出科时间 from (select CASEID,BEGINTIME as 入科时间,DEPT as 科室,ENDTIME as 出科时间 from department where caseid in(select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) order by BEGINTIME) t1,s_departments t2 where t1.科室=t2.code and t2.LABEL not like'%眼%'",
#   "all_antis": "select distinct ANAME as 抗菌药物 from ANTIBIOTICS where caseid in (select CASEID from overall where OUT_TIME>=:1 and IN_TIME<=:2) and substr(BEGINTIME,1,4)>'1900' and substr(BEGINTIME,1,4)<'2022' and substr(ENDTIME,1,4)>'1900' and substr(ENDTIME,1,4)<'2022'",
#   "begintime": "2018-01-01 00:00:00",
#   "endtime": "2018-02-01 00:00:00",
#   "process": "1",
#   "is_oracle": "1"
# }