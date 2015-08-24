pydnsproxy通过TCP请求避免运营商dns投毒污染

使用方法
Windows
1. 下载pydnsproxy，安装在你喜欢的位置。（注：Windows Vista/7 的用户请使用管理员模式安装）

2. 将宽带连接（或者其他你喜爱的名字的连接）的dns服务器设置为127.0.0.1

3. Enjoy it!

Linux、Mac
目前没有针对Linux和Mac的包，但可以把python的源码checkout下来，除需要手动设置外，使用方法类似于Windows。

说明
什么是DNS缓存污染？参见维基百科的这篇条目https://zh.wikipedia.org/wiki/%E5%9F%9F%E5%90%8D%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%BC%93%E5%AD%98%E6%B1%A1%E6%9F%93

DNSProxy只提供绕过DNS缓存污染的功能，而不能为你解决连接被重置的问题，更不能为你提供代理服务器翻墙。其他业务，请查询goagent。
