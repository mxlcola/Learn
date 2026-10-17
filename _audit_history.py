import subprocess,re
titles=['调整饮食结构','七日平均体重','正念饮食','减肥系统','运动微目标','GLP-1类减重药物']
for title in titles:
    path='tiddlers/'+title+'.tid'
    commits=subprocess.check_output(['git','log','--format=%H','--all','--',path],text=True).splitlines()
    print('###',title)
    for commit in commits[:7]:
        raw=subprocess.check_output(['git','show',commit+':'+path],stderr=subprocess.DEVNULL).decode('utf-8','ignore')
        parts=re.split(r'\r?\n\s*\r?\n',raw,maxsplit=1)
        body=parts[1] if len(parts)>1 else ''
        flag='placeholder' if '本条内容需要结合连续趋势' in body else ''
        print(commit[:8],len(body),flag)
