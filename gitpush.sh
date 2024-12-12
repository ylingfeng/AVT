#!/bin/bash

# git branch			# 查看当前分支
# git checkout master		# 进入提交分支
git add .          # 添加当前分支的修改内容到暂存区
git commit -m "$1" # 提交到版本库
# git pull origin gh-pages		# 拉取最新线上版本
# git merge master		# 把本地分支合并进去
git push -u origin gh-pages # 提交到线上
