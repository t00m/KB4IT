import json
repo = {}
repo['theme'] = 'techdoc'
repo['title'] = 'Repository for KB4IT testing'
repo['source'] = '$USER/Documents/repo/source/'
repo['target'] = '$USER/Documents/repo/target/'
repo['sort'] = ['Published', 'Updated']
repo['events'] = ['Change', 'Diary', 'Email', 'Incident', 'Message', 'Meeting', 'Note', 'Post', 'Procedure', 'Reminder', 'Report', 'Task']
repo['ignored_keys'] = ['Published', 'Updated']
repo['date_attributes'] = ['Date', 'Updated', 'Published']
repo['git_server'] = ''
repo['git_user'] = ''
repo['git_repo'] = ''
repo['git_branch'] = ''
repo['git_path'] = ''
repo['logging'] = 'INFO'
repo['force'] = True

with open('repo.json', 'w') as conf:
    json.dump(repo, conf, indent=4)