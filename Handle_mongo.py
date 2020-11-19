import pymongo

class mongoclient():
    def __init__(self):
        myclient = pymongo.MongoClient(host="localhost",port=27017)
        self.mydb = myclient['bilibili_info']

    def insert_data(self,collection_name,data):
        collection = self.mydb[collection_name]
        data = dict(data)
        if collection_name == 'bilibili_pindao':
            try:
                collection.find_one_and_delete({"pindao_id":data['pindao_id']})
                collection.insert_one(data)
                print("当前更新的数据为：%s" % data)
            except:
                collection.insert_one(data)
                print("当前插入的数据为：%s" % data)
        elif collection_name == 'bilibili_video':
            try:
                collection.find_one_and_delete({"bvid":data['bvid']})
                collection.insert_one(data)
                print("当前更新的数据为：%s" % data)
            except:
                collection.insert_one(data)
                print("当前插入的数据为：%s" % data)
        elif collection_name == 'bilibili_author':
            try:
                collection.find_one_and_delete({"author_id":data['author_id']})
                collection.insert_one(data)
                print("当前更新的数据为：%s" % data)
            except:
                collection.insert_one(data)
                print("当前插入的数据为：%s" % data)

mongo = mongoclient()