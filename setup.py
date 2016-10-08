#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import hashlib
import json
import logging
import time
import pymongo

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web 
from tornado.options import define, options, escape

define("port", default=4001, help="run on the given port", type=int)

# 数据库名称
DB_NAME = "test"

# 允许发起请求的host列表
HOST_ACCEPT_LIST = ["127.0.0.1:4001"]

class Application(tornado.web.Application):
	def __init__(self):

		# 连接mongodb数据库
		self.db = pymongo.MongoClient('localhost',27017)[DB_NAME]

		handlers = [
			(r"/", MainHandler)
		]
		settings = {
			"debug"	: True,
		}
		tornado.web.Application.__init__(self, handlers, **settings)

# 基础类
class BaseHandler(tornado.web.RequestHandler):

	def db_find_one(self, coll, param):
		return self.application.db[coll].find_one( param )

	def db_update(self, coll, param, data, upsert=False):
		return self.application.db[coll].update(param, {"$set":data}, upsert)


# RESTful API接口实现类
class ApiHandler(BaseHandler):

	# 预处理header，允许跨域
	def set_default_headers(self):
		self.set_header('Access-Control-Allow-Origin', '*')
		# self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
		self.set_header('Access-Control-Max-Age', 1000)
		self.set_header('Access-Control-Allow-Headers', '*')
		

	def update_access_token(self, access_account, access_type):
		secret_key = "__YOUR_KEY__"
		access_create = int(time.time())

		# 使用下面四个参数生成 new_token
		tmpArr = [secret_key, access_account, access_type, str(access_create)]
		tmpArr.sort()
		sha1 = hashlib.sha1()
		map(sha1.update,tmpArr)
		new_token = sha1.hexdigest()

		# 向客户端返回 new_token
		self.set_header("New-Token", new_token)

		# 将新token更新到数据库
		self.db_update("user", {"account":access_account}, {"access_token":new_token,"access_create":access_create})


	def finish(self, chunk=None, info=""):
		if chunk:
			response = {"meta":{"code":200, "info":info}, "data":chunk}

		else:
			if info is "":
				response = {"meta":{"code":404, "info":"not found"},"data":{}}
			else:
				response = {"meta":{"code":403, "info":info} , "data":{}}
			
		callback = tornado.escape.to_basestring(self.get_argument("callback", None))

		# 兼容jsonp请求
		if callback:

			# 直接发送js代码段发起执行
			# self.set_header("Content-Type", "application/x-javascript")

			# 发送数据文本，需要前端再处理
			self.set_header("Content-Type", "text/html")

			response = "%s(%s)"%(callback, tornado.escape.json_encode(response))

		else:
			# 直接发送json
			# self.set_header("Content-Type", "application/json; charset=UTF-8")

			self.set_header("Content-Type", "text/html")
		
		super(ApiHandler, self).finish(response)

# 请求权限处理类
class AccessHandler(ApiHandler):
	def prepare(self):

		# 获取请求头，并对请求头做做处理
		headers = self.request.headers
		if not self.ckeck_access_token(headers):

			# 不通过则返回禁止信息
			self.finish(chunk=None, info="access forbidden")
		else:
			return

	def ckeck_access_token(self, headers):

		# 判断host是否合法
		if "Host" in headers and headers["Host"] in HOST_ACCEPT_LIST:
			user_host = headers["Host"]
		else:
			return False

		# 判断token
		if ("Access-Type" and "Access-Token" and "Access-Account") in headers:
			access_type = headers["Access-Type"]
			access_token = headers["Access-Token"]
			access_account = headers["Access-Account"]

			logging.info(access_token)
			
			# 自定义字段 access_type
			if access_type == "__YOUR_TYPE__":

				# 查询数据库
				cont = self.db_find_one("user", {"account": access_account})
			else:
				return False

			if cont["access_token"] == access_token:

				# token有效期7200秒
				# 其中，在过期前10分钟有获取新token资格
				# 一旦获得新token，旧token立即废弃
				if int(time.time()) <= int(cont["access_create"]) + 7200:

					# 如果token合法且即将过期，则更新
					if int(time.time()) > int(cont["access_create"]) + 6600:
						# 生成新的token
						self.update_access_token(access_account, access_type)
					return True

		# 执行到最后还不返回True就说明token错误 
		return False
		
# 请求处理类
class MainHandler(AccessHandler):
	# 在相应的请求做完处理后，给客户端返回数据，此时回复头已经处理完毕

	def head(self):
		self.finish(chunk={"method":0}, info="head method")

	def get(self):
		self.finish(chunk={"method":1}, info="get method")

	def post(self):
		self.finish(chunk={"method":2}, info="post method")

	def delete(self):
		self.finish(chunk={"method":3}, info="delete method")

	def patch(self):
		self.finish(chunk={"method":4}, info="patch method")

	def put(self):
		self.finish(chunk={"method":5}, info="put method")

	def options(self):
		self.finish(chunk={"method":6}, info="options method")

# 入口函数		
def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()