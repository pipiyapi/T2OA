from ner import *
json_result=json_load("ner第五轮.json")
list_result=[]
for key,value in json_result.items():
    dict_item={}
    dict_item["id"]=key
    dict_item["result"]=value
    list_result.append(dict_item)
json_save(list_result,"ner结果.json")

