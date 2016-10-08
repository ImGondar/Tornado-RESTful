## Tornado-RESTful

### 简介

使用`Tornado`写`RESTful`接口。并支持json与jsonp格式

### 使用方法

#### 3个基础类

##### BaseHandler(tornado.web.RequestHandler)
继承自`RequestHandler`，内部集成数据库处理相关函数，以及一些常用的处理函数等等
继承自此类的Handler可以原生的使用Tornado的相关方法

##### ApiHandler(BaseHandler)
继承自`BaseHandler`，内部实现RESTful API返回数据的方法。
其中`set_default_headers()`：设置允许跨域访问；`update_access_token()`:用于生成`Access-Token`；`finish()`:复写，用于返回json或jsonp格式的数据

继承此类的Handler可以用RESTful方式返回数据，并且不会被检查`Access-Token`，并且可以给返回的headers中添加`New-Token`字段。
一般来说，适合注册、登录等用于向服务器请求授权的操作，或者无需授权的操作。

##### AccessHandler(ApiHandler)
继承自ApiHandler，内部复写了`prepare()`方法，用于在正式处理请求前验证用户权限，即headers中的三个字段`Access-Type`、`Access-Token`、`Access-Account`,如果不合法则直接返回错误。并且对合法的`Access-Token`进行更新维护。

#### 数据库
本程序使用的数据库是Mongodb。默认位置为`localhost:27017`。可以设置`DB_NAME = "test"`来修改数据库名称。
默认的数据库结构如下：
```python
test # 数据库名

user # 用户数据表

{
	"account": "123456789@xy.com",
	"access_token": "b0d5a67400024e86",
	"access_create": 1475700000,
	"username":"...",
	"password":"...."
}

...  # 其他数据表

```

#### 使用jsonp请求
客户端的请求带上callback参数就可以实现jsonp格式返回。
例如：
```
普通请求：
[GET] 127.0.0.1:4001

[RESPOSE] {"meta":{"code":200,"info":"get method"},"data":{"method":0}}
```

```
使用jsonp请求：
[GET] 127.0.0.1:4001?callback=handler

[RESPOSE] handler({"meta":{"code":200,"info":"get method"},"data":{"method":0}})
```

### 注意事项
无

### 更新版本
无