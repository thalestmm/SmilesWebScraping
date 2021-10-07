# IMPORTING MAIN LIBRARIES
from bs4 import BeautifulSoup
import requests
import re


#  GET MAIN USER INPUTS (SELECTED PRODUCT AND AVG MILE PRICING)
prod = input("Qual produto você quer procurar? ")
milheiro = int(input('Valor do milheiro SMILES: '))

# VERIFY TARGET E-MAIL
testing = input(r"Enviar pro TAL? (S/N) ")

if testing.upper() == "S":
    target_email = "meier.thales@gmail.com"
else:
    target_email = input("Digite o seu e-mail: ")


# PONTUAÇÃO DO CARTÃO (JÁ COM BÔNUS DA SMILES)
smiles_bonus = 1.8
pont_card = 2.5 * smiles_bonus


# USD/BRL QUOTE TO RETRIEVE CREDIT CARD POINTS
url_usd = "https://br.advfn.com/bolsa-de-valores/fx/USDBRL/grafico"
page_usd = requests.get(url_usd).text
doc_usd = BeautifulSoup(page_usd,"html.parser")

usdbrl = float(doc_usd.find_all(class_=re.compile(f"PriceText.*"))[-1].text.replace(',','.'))

pont_card = usdbrl * smiles_bonus
# INITIAL SETUP
url = f"https://www.shoppingsmiles.com.br/smiles/super_busca.jsf?b={prod}&a=true"
page = requests.get(url).text
doc = BeautifulSoup(page,"html.parser")
price_list = []


# PAGE NAVIGATION
product_panel = doc.find(class_="itens-section")
item_boxes = product_panel.find_all(class_=re.compile(f"box-item-link produto_.*"))

# START SCRAPING
for item in item_boxes:
    # TREE NAVIGATION TO FIND SPECIFIC TAGS
    produto = item.find(class_="box-produto").find('div')
    milhas = int(produto.find(class_=re.compile(f'clube-section-box--clube clube-section-box.*')).find('span')
                 .find('span').find_all(class_="clube-section-text-bold")[2].string.replace('.',''))
    link = 'https://www.shoppingsmiles.com.br' + produto.find('a')['href']
    prod_price = float(produto.find('a').find_all(class_='preco-por preco-por-acumulo')[2].string
                       .replace('.','').replace(',','.'))
    nome = produto.find('a').find(class_=re.compile(f'name-promocao-section-box.*')).find('span').string

    # NEW VARIABLES FROM THE SCRAPED DATA
    price_desc = prod_price - ((milhas/1000)*milheiro)
    porc_desc = ((prod_price - price_desc)/prod_price)*100
    usd_price = prod_price/usdbrl
    desc_full = price_desc - ((usd_price*pont_card/1000)*milheiro)
    desc_nub = price_desc - ((prod_price/4000)*milheiro)

    # PRODUCT DATA INSERTION INTO THE LIST
    price_list.append({
        "NOME":nome,
        "PREÇO":prod_price,
        "DESCONTADO":price_desc,
        "DESC FULL":desc_full,
        "NUBANK":desc_nub,
        "PORCENTAGEM":porc_desc,
        "MILHAS":milhas,
        "LINK":link
    })

# SORT LIST FROM DISCOUNTED PRICES, IN ASCENDING ORDER
price_list.sort(key=lambda x: x["DESCONTADO"])

# CREATE THE MESSAGE TO BE SENT VIA EMAIL
from datetime import date
day_today = date.today()

mail_subject = f'Preços de {prod.upper()} - {day_today}'

def create_message(price_list):
    message = f'Esses são os preços de {prod.upper()} para o dia {day_today}:\n'
    for i in price_list[0:8]: # ONLY DISPLAY 8 PRODUCTS
        message+='\n \n'
        message+= i["NOME"] + ' - R$' + str(round(i["PREÇO"], 2)) + ' - COM DESCONTO: R$' + \
                  str(round(i["DESCONTADO"], 2))
        message += r' / R$' + str(round(i["DESC FULL"], 2)) + r' / R$' + str(round(i["NUBANK"], 2)) + ' - '
        message+= str(round(i["PORCENTAGEM"], 2)) + '% DE DESCONTO E ' + str(i["MILHAS"]) + ' MILHAS. \n'
        message+= 'LINK: ' + i["LINK"] + '\n'

    return message

def create_html_message(price_list):
    message = '<body style="font-family:Lato">'
    message += f'<h3>Esses são os preços de {prod.upper()} para o dia {day_today}:</h3>'
    for i in price_list[0:8]:
        message+='<br>'
        message += i["NOME"] + ' - R$' + str(round(i["PREÇO"], 2)) + ' - COM DESCONTO: <strong>R$' + \
                   str(round(i["DESCONTADO"], 2))
        message += r' / R$' + str(round(i["DESC FULL"], 2)) + r' / R$' + str(round(i["NUBANK"], 2)) + '</strong> - '
        message += str(round(i["PORCENTAGEM"], 2)) + '% DE DESCONTO E ' + str(i["MILHAS"]) + ' MILHAS.'
        message+='<br>'
        message += 'LINK: ' + i["LINK"]
        message+='<br><br>'
    message+='</body>'

    return message


# EMAIL SETUP
import win32com.client as win32
outlook = win32.Dispatch('Outlook.application')
mail = outlook.CreateItem(0)
mail.To = target_email
mail.Subject = mail_subject
#mail.Body = create_message(price_list)
mail.HTMLbody = create_html_message(price_list)

mail.Send()

print("\nDone!")
