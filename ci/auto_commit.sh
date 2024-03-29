#!/bin/sh

# Shell script originally by Canadian Digital Service – Service numérique canadien.
# 
# Only this file in licensed under the license text below.
# 
# ======Begin license text.
# 
# MIT License
# 
# Copyright (c) 2019 Canadian Digital Service – Service numérique canadien
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# ======End license text.

# Git Config
git config --global user.name "${GITHUB_ACTOR} (CI)"
git config --global user.email "${GITHUB_ACTOR}@users.noreply.github.com"
# Add files
git add -A
# Only commit if there are changes.
git diff --quiet && git diff --staged --quiet || git commit -m "$1" --allow-empty
# Pull & Push
git pull
git push -u origin HEAD
