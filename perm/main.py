 #!/usr/bin/env python
 # -*- coding: utf-8 -*-

import requests 
from requests import Request, Session
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
import requests
from requests import Request, Session
import pandas as pd
import numpy as np
from selenium import webdriver
from time import sleep
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
import re
import torch
from transformers import AutoModelForSequenceClassification
from transformers import BertTokenizerFast
import json
list_words_accepted = ['победитель']

tokenizer = BertTokenizerFast.from_pretrained('blanchefort/rubert-base-cased-sentiment')
model = AutoModelForSequenceClassification.from_pretrained('blanchefort/rubert-base-cased-sentiment', return_dict=True)
pos_tags = set(['Отчетность',
  'Отзывчивые люди',
  'Фонд',
  'Больные дети',
  'Помощь',
  'Дело'])
  
  

def check_mailru(fond, inn):
    po = fond.replace(' ', '+')
    urls = f'https://dobro.mail.ru/funds/search/?query={po}&recipient=all&city=any'
    response = requests.get(urls)
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('div', class_='cols__column cols__column_small_percent-100 cols__column_medium_percent-50 cols__column_large_percent-50')
    if len(quotes) != 0:
        check_on = []
        for i in range(len(quotes)):
            name = str(quotes[i].find('span', 'link__text'))
            name = name.replace('<span class="link__text">', '')
            name = name.replace('</span>', '')

            url = str(quotes[i].find('a', 'link link_font_large margin_bottom_10 link-holder'))
            url = url.replace('<a class="link link_font_large margin_bottom_10 link-holder" href="', 'https://dobro.mail.ru')
            url = url.split('"')[0]

            city = str(quotes[i].find('div', 'p-fund__city margin_bottom_5'))
            city = city.replace('<div class="p-fund__city margin_bottom_5">', '')
            city = city.replace('</div>', '')

            responses = requests.get(url)
            soups = BeautifulSoup(responses.text, 'lxml')

            site = soups.find_all('div', class_='p-fund-detail__info-row')
            if str(site[0].find('a', 'link')) != None:
                site = str(site[0].find('a', 'link'))
                site = site.replace('<span class="link__text">', '')
                site = site.replace('</span>', '')
            else:

                site = str(site[1].find('a', 'link'))
                site = site.replace('<span class="link__text">', '')
                site = site.split('"')[3]

            check_on.append(name + '\n' + city + '\n' + url + '\n' + site + '\n')
        return check_on
    else:
        return 'Not Found'

def check_Nuzhna_pomosh(fond, inn):
    url = 'https://nuzhnapomosh.ru/wp-content/plugins/nuzhnapomosh/funds.php'
    typ = 'POST'
    req = Request(typ, url, files = {'np_name': (None, fond)}).prepare()
    s = Session()
    respo = s.send(req)
    respo.text
    soup2 = BeautifulSoup(respo.text, 'lxml')
    quotes2 = soup2.find_all('div', class_='np-card__inner')
    if len(quotes2) != 0:
        check_on = []
        for i in range(len(quotes2)):
            name = str(quotes2[i].find('h4', 'np-card__title'))
            name = name.replace('<h4 class="np-card__title">', '')
            name = name.replace('</h4>', '')

            descr = str(quotes2[i].find('p', 'np-card__descr'))
            descr = descr.replace('<p class="np-card__descr">', '')
            descr = descr.replace('</p>', '')

            money = str(quotes2[i].find('li', 'np-card__row'))
            money = money.split('<span>')[1]
            money = money.replace('</li>', '')
            money = money.replace(' ₽</span>', '')
            money = money.replace('\n', '')

            site = str(quotes2[i].find('a', 'np-card__link'))
            site = site.replace('<a class="np-card__link" href="', '')
            site = site.split('"')[0]

            check_on.append(name + '\n' + descr + '\n' + 'Деньги в фонде: ' + money + ' Рублей' + '\n' + 'https://nuzhnapomosh.ru' + site + '\n')
        return check_on
    else:
        return 'Not Found'
        
def check_wse_wmeste(fond, inn):
    with open('wse_vmeste.txt', 'r') as fin:
        for i in fin.readlines():
            if i.lower().strip()==fond.lower().strip():
                return True
    return False        
        

def check_prezidentgrants(fond, inn):
    with webdriver.Remote("http://173.17.206.247:4444/wd/hub", DesiredCapabilities.CHROME) as driver:
        driver.get('https://президентскиегранты.рф/public/application/cards')
        elem = driver.find_elements_by_id('SearchString')
        if len(elem) > 0:
            elem[0].send_keys(str(inn))
        elem = driver.find_elements_by_class_name('projects__btn-submit')
        if len(elem) > 0:
            elem[0].click()
        sleep(1)
        elem = driver.find_elements_by_class_name("projects__table")
        if len(elem)>0:
            items = elem[0].find_elements_by_tag_name('a')
            url = items[0].get_attribute('href')
            elem[0].click()
        else:
            return 'Not Found'
        sleep(1)
        elem = driver.find_element_by_class_name("winner-info__status")
        text = elem.text.split(':')[1].split()
        return url, text

def get_reviews_yandex(name, inn):
    with webdriver.Remote("http://173.17.206.247:4444/wd/hub", DesiredCapabilities.CHROME) as driver:
        result = {}
        result['name'] = name
        result['tags'] = []
        result['reviews'] = []
        driver.get('https://yandex.ru')
        elem = driver.find_elements_by_id('text')
        if len(elem) > 0:
            elem[0].send_keys(name)
        elem = driver.find_elements_by_class_name('search2__button')
        sleep(1)
        if len(elem) > 0:
            elem[0].click()
        sleep(3)
        elem = driver.find_elements_by_css_selector('span.Link_pseudo:nth-child(1)')
        if len(elem) > 0:
            elem[0].click()
        sleep(3)
        html = driver.page_source
        tags = [x.split('<')[0] for x in html.split('class="Button2-Text">')[1:-1]]
        if 'Оставить отзыв' in tags:
            tags = tags[tags.index('Оставить отзыв') + 1:]
        if 'Оставить отзыв' in tags:
            tags = tags[tags.index('Оставить отзыв') + 1:]
        result['tags'] = [x for x in tags if len(x) > 0][:10]
        reviews = [''.join([x.split('>')[1] for x in x.split('<')[1::2] if len(x.split('>')) > 1 and len(x.split('>')[1]) > 0]) for x in html.split('Cut TextCut')[1:-1]]
        result['reviews'] = [re.sub('{.+?}', '', x).split('Читать все отзывы')[0].split('Скрыть')[0] for x in reviews]
        result['mark'] = [x.split()[0].strip() for x in html.split('aria-label="Рейтинг: ')[1:]][0]
        return result
    
    
def check_minUst(fond, inn):
    with webdriver.Remote("http://173.17.206.247:4444/wd/hub", DesiredCapabilities.CHROME) as driver:
        driver.get('http://unro.minjust.ru/NKOs.aspx')
        elem = driver.find_element_by_name('filter_org_name')
        elem.send_keys(fond)
        elem = driver.find_element_by_name('b_refresh')
        elem.click()
        sleep(3)
        elem = driver.find_element_by_id('pdg')
        elem = elem.find_element_by_class_name('pdg_pos')
        if int(elem.text[17:].split()[0])>0:
            return True
        else:
            return False
            
            
def get_news_yandex(fond, inn):
    if 'фонд' not in fond.lower():
        fond = 'фонд ' + fond
    url = 'https://newssearch.yandex.ru/news/search?text=' + fond.replace(' ', '+')
    response = requests.get(url)
    html = response.text
    headers = [x for x in [x.split('"text">')[1].split('<')[0] for x in html.split('mg-snippet__url')[1:]] if len(x) >0]
    return headers            

@torch.no_grad()
def predict(text):
    inputs = tokenizer(text, max_length=512, padding=True, truncation=True, return_tensors='pt')
    outputs = model(**inputs)
    predicted = torch.nn.functional.softmax(outputs.logits, dim=1)
    res = torch.argmax(predicted, dim=1).numpy().astype(int)
    negs = []
    poss=[]
    for i in range(len(predicted)):
        if predicted[i][2] > 0.1:
            negs.append((text[i],float(predicted[i][2])))
        elif predicted[i][1]>0.1:
            poss.append((text[i], float(predicted[i][1])))
    return negs, poss
    
def check_nalog(fond, inn):
    inn = str(inn)
    site = "https://egrul.nalog.ru/index.html"
    print(inn)
    #chrome_options = Options()
    #chrome_options.add_argument("--headless")

    #driver = webdriver.Chrome(options=chrome_options)
    with webdriver.Remote("http://173.17.206.247:4444/wd/hub", DesiredCapabilities.CHROME) as driver:
        driver.get(site)

        driver.find_element_by_xpath("//div[@class='inp-nalog input-text txt-wide txt-string']").click()
        driver.find_element_by_xpath("//input[@class='txt-wide txt-string']").send_keys(inn)
        driver.find_element_by_xpath("//button[@id='btnSearch']").click()
        time.sleep(1)
        try:
            driver.find_element_by_xpath("//button[@class='btn-with-icon btn-excerpt op-excerpt']")
            return True
        except:
            return False

def get_google_titles_subtitles(name, inn):
    if 'фонд' not in name.lower():
        name = 'фонд ' + name
    with webdriver.Remote("http://173.17.206.247:4444/wd/hub", DesiredCapabilities.CHROME) as driver:
        driver.get('https://google.com')
        elem = driver.find_element_by_css_selector('.gLFyf')
        elem.send_keys(name)
        sleep(2)
        elem.send_keys(Keys.ENTER)
        sleep(3)
        elem = driver.find_element_by_xpath("//*[contains(text(), 'Новости')]")
        elem.click()
        sleep(2)
        titles = [driver.find_element_by_xpath(f'/html/body/div[7]/div/div[9]/div[1]/div/div[2]/div[2]/div/div/div[{i}]/g-card/div/div/a/div/div[2]/div[2]').text.replace('\n', ' ').replace('...', '') for i in range(1,8)]
        subtitles = [driver.find_element_by_xpath(f'/html/body/div[7]/div/div[9]/div[1]/div/div[2]/div[2]/div/div/div[{i}]/g-card/div/div/a/div/div/div[3]').text.replace('\n', ' ').replace('...', '') for i in range(1,8)]
    return [titles, subtitles] 

def  get_news_google(name, inn):
    return get_google_titles_subtitles(name, inn)
    
    
    
from multiprocessing import Pool
crawlers = [check_mailru, check_Nuzhna_pomosh, check_wse_wmeste, check_prezidentgrants, check_minUst, check_nalog, get_news_yandex, get_news_google, get_reviews_yandex]

def exec_crawler(a):
    func = crawlers[a["func"]]
    fond, inn = a["fond"], a["inn"]
    try:
        res = func(fond,inn)
    except Exception as e:
        res = None
        print(func.__name__, repr(e))
    return res

def all_check_fond(fond, inn):
    

        
    f_crawlers = []
    for i in range((len(crawlers))):
        d = {}
        d["func"] = i
        d["fond"] = fond
        d["inn"] = inn
        f_crawlers.append(d)
    #fcrawlers = list(map(check_wrapper, crawlers))
    with Pool(4) as p:
        lst = p.map( exec_crawler, f_crawlers)
    result_mail, result_nuzhna_pom, result_wse_wmeste, result_prezidentgrants, result_minust, result_nalog, news_yandex, gogl, reviews = lst
    
    if gogl is not None:
        titles_google,news_google = gogl
    else:
        titles_google,news_google = None, None
    
    
    if news_google is not  None:
        neg_go, pos_go = predict(news_google)
    else:
        neg_go, pos_go = None, None
         
    if titles_google is not  None:
        title_neg_go, title_pos_go = predict(titles_google)
    else:
        title_neg_go, title_pos_go = None, None    
        
    
    if news_yandex is not  None:
        if len(news_yandex)>0: 
            negs_ya, pos_ya = predict(news_yandex)
        else:
            negs_ya, pos_ya = None, None
    else:
        negs_ya, pos_ya = None, None
        
    if reviews is not None:
        mark = reviews['mark']
        rev_neg, rev_pos = predict(reviews['reviews'])
    else:    
        mark = None
        rev_neg, rev_pos = None, None
   #titles_google,news_google
    tags = ['tags']
    count_pos_tags=0
    for i in tags:
        count_pos_tags+=(i in pos_tags)

   
    
 
    final_result = {}
    final_result["negs_ya"] = negs_ya
    final_result["pos_ya"] = pos_ya
    final_result["negs_go"] = neg_go
    final_result["pos_go"] = pos_go
    final_result["title_neg_go"] = title_neg_go
    final_result["title_pos_go"] = title_pos_go
    final_result["rev_pos"] = rev_pos
    final_result["rev_neg"] = rev_neg
   
    final_result["result_minust"] = result_minust
    final_result["result_mail"] = result_mail
    final_result["result_nuzhna_pom"] = result_nuzhna_pom
    final_result["result_wse_wmeste"] = result_wse_wmeste
    final_result["result_prezidentgrants"] = result_prezidentgrants
    final_result["result_minust"] = result_minust
    final_result["result_nalog"] = result_nalog
    final_result["news_yandex"] = news_yandex
    final_result["reviews"] = reviews
    final_result["mark"] = mark
    
    
    clf_result = classificator(final_result)
    
    final_repr = {}

    final_repr["RESULT"] = float(clf_result)
    final_repr["Отзывы Google"] = {}
    final_repr["Отзывы Google"]["+"] = pos_go
    final_repr["Отзывы Google"]["-"] = neg_go
    
    final_repr["Новости Google"] = {}
    final_repr["Новости Google"]["+"] = title_pos_go
    final_repr["Новости Google"]["-"] = title_neg_go

    final_repr["Новости яндекс"] = {}
    final_repr["Новости яндекс"]['+'] = pos_ya   
    final_repr["Новости яндекс"]['-'] = negs_ya 
   
    final_repr["Минюст"] = result_minust
    final_repr["Mail.ru"] = result_mail
    final_repr["Нужна помощь"] = result_nuzhna_pom
    final_repr["Все вместе"] = result_wse_wmeste
    final_repr["Гранты Президента"] = result_prezidentgrants
    
    final_repr["ФНС"] = result_nalog
    
    final_repr["Отзыва Яндекс"] = reviews
    final_repr["Оценка по отзывам Яндекс"] = mark
    
    return clf_result, final_repr
    
    




def classificator(args_dict):
    if ((args_dict['result_nuzhna_pom'] != 'Not Found' and args_dict['result_nuzhna_pom'] is not None)
      #  or args_dict['all']
        or args_dict['result_minust']
        or args_dict['result_nalog']):
        return 1
    elif args_dict['result_prezidentgrants'] is not None:
        for word in list_words_accepted:
            if word in args_dict['result_prezidentgrants'][1]:
                return 1


    tmp_res_rev = 0.0
    tmp_count = 0
    if args_dict['rev_neg'] is not None:
        for tmp in args_dict['rev_neg']:
            tmp_res_rev -= tmp[1]
            tmp_count += 1
    if args_dict['rev_pos'] is not None:
        for tmp in args_dict['rev_pos']:
            tmp_res_rev += tmp[1]
            tmp_count += 1
    tmp_res_rev /= (tmp_count + 1 * (tmp_count == 0))


    tmp_res_title = 0.0
    tmp_count = 0
    if args_dict['title_neg_go'] is not None:
        for tmp in args_dict['title_neg_go']:
            tmp_res_title -= tmp[1]
            tmp_count += 1
    if args_dict['title_pos_go'] is not None:
        for tmp in args_dict['title_pos_go']:
            tmp_res_title += tmp[1]
            tmp_count += 1
    tmp_res_title /= (tmp_count + 1 * (tmp_count == 0))

    tmp_res_ya = 0.0
    tmp_count = 0
    if args_dict['negs_ya'] is not None:
        for tmp in args_dict['negs_ya']:
            tmp_res_ya -= tmp[1]
            tmp_count += 1
    if args_dict['pos_ya'] is not None:
        for tmp in args_dict['pos_ya']:
            tmp_res_ya += tmp[1]
            tmp_count += 1
    tmp_res_ya /= (tmp_count + 1 * (tmp_count == 0))
    
    tmp_res_go = 0.0
    tmp_count = 0
    if args_dict['negs_go'] is not None:
        for tmp in args_dict['negs_go']:
            tmp_res_go -= tmp[1]
            tmp_count += 1
    if args_dict['pos_go'] is not None:
        for tmp in args_dict['pos_go']:
            tmp_res_go += tmp[1]
            tmp_count += 1
    tmp_res_go /= (tmp_count + 1 * (tmp_count == 0))
    
    return float((tmp_res_ya * 0.3 + tmp_res_go * 0.2 +tmp_res_rev * 0.4 +tmp_res_title * 0.1+ 1) / 2)




from flask import Flask, render_template, request, escape, Markup
app = Flask(__name__)
 
@app.route('/')
def main_page():
    return 'OK'
    
from json2html import *
   
@app.route('/charity/', methods=['post', 'get'])
def charity():
    message = ''
    final_scores_str = ''
    if request.method == 'POST':
        name = request.form.get('orgname')  # запрос к данным формы
        inn = request.form.get('inn')
        print(name, inn)
        #if len(inn)>0:
            
        final_scores, res = all_check_fond(name, inn)
        final_scores_str = str(final_scores)
        #print(res)
        #message = Markup(escape(json.dumps(res, indent=4, ensure_ascii=False)).replace("\n", "<br/>"))
        message = Markup(json2html.convert(json=res))
        #for line in str(json.dumps(res, indent=4, ensure_ascii=False)).split("\n"):
        #    message += Markup.escape(line) + Markup('<br />')
        
   
    if request.method == 'GET':   
        name = request.args.get('orgname')  # запрос к данным формы
        inn = request.args.get('inn')
        print(name, inn)
        if name is not None:
            print(name, inn)
            #if len(inn)>0:
                
            final_scores, res = all_check_fond(str(name), str(inn))
            final_scores_str = str(final_scores)
            #print(res)
            message = Markup(escape(json.dumps(res, indent=4, ensure_ascii=False)))
   
            return render_template('raw.html', final_scores = final_scores, message=message)

    return render_template('main.html', final_scores = final_scores_str, message=message)
 

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')