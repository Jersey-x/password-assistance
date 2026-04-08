# Password-Assistance

这是一个基于 Python 开发的密码辅助工具，支持自动更新检查与本地加密存储.

## 功能特性 (Features)

将键盘的F1-F9键对应到相应密码，实现快速输入复杂密码，适用于频繁需要输入密码的场景。

## 用法（Usage）

在运行本项目之前，请确保你的电脑已安装Python3.14

#### 克隆项目到本地
```shell git clone https://github.com/Jersey-x/password-assistance.git
git clone https://github.com/Jersey-x/password-assistance.git 
````
#### 进入目录
```shell
cd repository
```

#### 安装依赖库
```shell
 git pip install -r requirements.txt
```
#### 运行程序
``` shell
python password.assistance.py
```
设置对应的密码，重启程序后使用对应F1~F9功能键，便可快速输入密码。密码在本地以pass_config.json形式保存。
也可以直接在release中下载打包好的.exe程序。
