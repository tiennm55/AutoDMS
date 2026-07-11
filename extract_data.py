2026-07-11T15:19:16.1213208Z Current runner version: '2.335.1'
2026-07-11T15:19:16.1239302Z ##[group]Runner Image Provisioner
2026-07-11T15:19:16.1240773Z Hosted Compute Agent
2026-07-11T15:19:16.1241402Z Version: 20260624.560
2026-07-11T15:19:16.1242149Z Commit: 925d229a51159bc391ae97e54a2dd1fe20af789d
2026-07-11T15:19:16.1242970Z Build Date: 2026-06-24T18:26:47Z
2026-07-11T15:19:16.1243715Z Worker ID: {58f163e8-c2f3-4822-ada7-c4d174ebf2ab}
2026-07-11T15:19:16.1244470Z Azure Region: westcentralus
2026-07-11T15:19:16.1245084Z ##[endgroup]
2026-07-11T15:19:16.1246669Z ##[group]Operating System
2026-07-11T15:19:16.1247502Z Ubuntu
2026-07-11T15:19:16.1248098Z 24.04.4
2026-07-11T15:19:16.1248651Z LTS
2026-07-11T15:19:16.1249176Z ##[endgroup]
2026-07-11T15:19:16.1249826Z ##[group]Runner Image
2026-07-11T15:19:16.1250741Z Image: ubuntu-24.04
2026-07-11T15:19:16.1251379Z Version: 20260705.232.1
2026-07-11T15:19:16.1252993Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20260705.232/images/ubuntu/Ubuntu2404-Readme.md
2026-07-11T15:19:16.1254720Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20260705.232
2026-07-11T15:19:16.1255796Z ##[endgroup]
2026-07-11T15:19:16.1257009Z ##[group]GITHUB_TOKEN Permissions
2026-07-11T15:19:16.1259285Z Contents: read
2026-07-11T15:19:16.1259966Z Metadata: read
2026-07-11T15:19:16.1260809Z Packages: read
2026-07-11T15:19:16.1261541Z ##[endgroup]
2026-07-11T15:19:16.1263739Z Secret source: Actions
2026-07-11T15:19:16.1264814Z Prepare workflow directory
2026-07-11T15:19:16.1670606Z Prepare all required actions
2026-07-11T15:19:16.1710308Z Getting action download info
2026-07-11T15:19:16.4758088Z Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
2026-07-11T15:19:17.0357691Z Download action repository 'actions/setup-python@v5' (SHA:a26af69be951a213d495a4c3e4e4022e16d87065)
2026-07-11T15:19:17.2362079Z Complete job name: convert_to_csv
2026-07-11T15:19:17.3305394Z Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
2026-07-11T15:19:17.3317411Z ##[group]Run actions/checkout@v4
2026-07-11T15:19:17.3318786Z with:
2026-07-11T15:19:17.3319713Z   repository: tiennm55/AutoDMS
2026-07-11T15:19:17.3329772Z   token: ***
2026-07-11T15:19:17.3331135Z   ssh-strict: true
2026-07-11T15:19:17.3332093Z   ssh-user: git
2026-07-11T15:19:17.3333039Z   persist-credentials: true
2026-07-11T15:19:17.3334095Z   clean: true
2026-07-11T15:19:17.3335065Z   sparse-checkout-cone-mode: true
2026-07-11T15:19:17.3336205Z   fetch-depth: 1
2026-07-11T15:19:17.3337114Z   fetch-tags: false
2026-07-11T15:19:17.3338077Z   show-progress: true
2026-07-11T15:19:17.3339040Z   lfs: false
2026-07-11T15:19:17.3339989Z   submodules: false
2026-07-11T15:19:17.3341123Z   set-safe-directory: true
2026-07-11T15:19:17.3342766Z ##[endgroup]
2026-07-11T15:19:17.4412375Z Syncing repository: tiennm55/AutoDMS
2026-07-11T15:19:17.4415568Z ##[group]Getting Git version info
2026-07-11T15:19:17.4417038Z Working directory is '/home/runner/work/AutoDMS/AutoDMS'
2026-07-11T15:19:17.4419123Z [command]/usr/bin/git version
2026-07-11T15:19:17.4468206Z git version 2.54.0
2026-07-11T15:19:17.4527411Z ##[endgroup]
2026-07-11T15:19:17.4546777Z Temporarily overriding HOME='/home/runner/work/_temp/65464a1e-6681-4483-a5c3-7d6a77749f44' before making global git config changes
2026-07-11T15:19:17.4552270Z Adding repository directory to the temporary git global config as a safe directory
2026-07-11T15:19:17.4556379Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/AutoDMS/AutoDMS
2026-07-11T15:19:17.4604637Z Deleting the contents of '/home/runner/work/AutoDMS/AutoDMS'
2026-07-11T15:19:17.4609466Z ##[group]Initializing the repository
2026-07-11T15:19:17.4613982Z [command]/usr/bin/git init /home/runner/work/AutoDMS/AutoDMS
2026-07-11T15:19:17.4733919Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-07-11T15:19:17.4737712Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-07-11T15:19:17.4741276Z hint: to use in all of your new repositories, which will suppress this warning,
2026-07-11T15:19:17.4743979Z hint: call:
2026-07-11T15:19:17.4745349Z hint:
2026-07-11T15:19:17.4747156Z hint: 	git config --global init.defaultBranch <name>
2026-07-11T15:19:17.4749317Z hint:
2026-07-11T15:19:17.4751604Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-07-11T15:19:17.4755229Z hint: 'development'. The just-created branch can be renamed via this command:
2026-07-11T15:19:17.4757875Z hint:
2026-07-11T15:19:17.4759328Z hint: 	git branch -m <name>
2026-07-11T15:19:17.4761166Z hint:
2026-07-11T15:19:17.4763402Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-07-11T15:19:17.4766922Z Initialized empty Git repository in /home/runner/work/AutoDMS/AutoDMS/.git/
2026-07-11T15:19:17.4773056Z [command]/usr/bin/git remote add origin https://github.com/tiennm55/AutoDMS
2026-07-11T15:19:17.4795762Z ##[endgroup]
2026-07-11T15:19:17.4798382Z ##[group]Disabling automatic garbage collection
2026-07-11T15:19:17.4802351Z [command]/usr/bin/git config --local gc.auto 0
2026-07-11T15:19:17.4849217Z ##[endgroup]
2026-07-11T15:19:17.4851599Z ##[group]Setting up auth
2026-07-11T15:19:17.4857416Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-07-11T15:19:17.4897273Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-07-11T15:19:17.5267650Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-07-11T15:19:17.5315466Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-07-11T15:19:17.5559557Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-07-11T15:19:17.5599476Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-07-11T15:19:17.5833638Z [command]/usr/bin/git config --local http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-07-11T15:19:17.5876603Z ##[endgroup]
2026-07-11T15:19:17.5878947Z ##[group]Fetching the repository
2026-07-11T15:19:17.5887194Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +3f2e55bb4a122bd1663e2d4ef6a2a40da05b912b:refs/remotes/origin/main
2026-07-11T15:19:19.3847353Z From https://github.com/tiennm55/AutoDMS
2026-07-11T15:19:19.3848376Z  * [new ref]         3f2e55bb4a122bd1663e2d4ef6a2a40da05b912b -> origin/main
2026-07-11T15:19:19.3883429Z ##[endgroup]
2026-07-11T15:19:19.3884279Z ##[group]Determining the checkout info
2026-07-11T15:19:19.3886451Z ##[endgroup]
2026-07-11T15:19:19.3893327Z [command]/usr/bin/git sparse-checkout disable
2026-07-11T15:19:19.3946516Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-07-11T15:19:19.3983036Z ##[group]Checking out the ref
2026-07-11T15:19:19.3986715Z [command]/usr/bin/git checkout --progress --force -B main refs/remotes/origin/main
2026-07-11T15:19:19.4383281Z Switched to a new branch 'main'
2026-07-11T15:19:19.4384615Z branch 'main' set up to track 'origin/main'.
2026-07-11T15:19:19.4392134Z ##[endgroup]
2026-07-11T15:19:19.4444574Z [command]/usr/bin/git log -1 --format=%H
2026-07-11T15:19:19.4474191Z 3f2e55bb4a122bd1663e2d4ef6a2a40da05b912b
2026-07-11T15:19:19.4746603Z Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
2026-07-11T15:19:19.4748734Z ##[group]Run actions/setup-python@v5
2026-07-11T15:19:19.4749022Z with:
2026-07-11T15:19:19.4749231Z   python-version: 3.9
2026-07-11T15:19:19.4749464Z   check-latest: false
2026-07-11T15:19:19.4752391Z   token: ***
2026-07-11T15:19:19.4752631Z   update-environment: true
2026-07-11T15:19:19.4752885Z   allow-prereleases: false
2026-07-11T15:19:19.4753120Z   freethreaded: false
2026-07-11T15:19:19.4753339Z ##[endgroup]
2026-07-11T15:19:19.6093968Z ##[group]Installed versions
2026-07-11T15:19:19.6172609Z Version 3.9 was not found in the local cache
2026-07-11T15:19:19.6284178Z (node:2397) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
2026-07-11T15:19:19.6285048Z (Use `node --trace-deprecation ...` to show where the warning was created)
2026-07-11T15:19:20.6162193Z Version 3.9 is available for downloading
2026-07-11T15:19:20.6162936Z Download from "https://github.com/actions/python-versions/releases/download/3.9.25-19039189640/python-3.9.25-linux-24.04-x64.tar.gz"
2026-07-11T15:19:21.4396255Z Extract downloaded archive
2026-07-11T15:19:21.4546412Z [command]/usr/bin/tar xz --warning=no-unknown-keyword --overwrite -C /home/runner/work/_temp/aafccd48-3432-4c46-bb86-40efcaf22c91 -f /home/runner/work/_temp/2aa65230-f178-4363-8144-f001d4b895d7
2026-07-11T15:19:22.8754245Z Execute installation script
2026-07-11T15:19:22.8846566Z Check if Python hostedtoolcache folder exist...
2026-07-11T15:19:22.8847265Z Create Python 3.9.25 folder
2026-07-11T15:19:22.8861370Z Copy Python binaries to hostedtoolcache folder
2026-07-11T15:19:23.3457996Z Create additional symlinks (Required for the UsePythonVersion Azure Pipelines task and the setup-python GitHub Action)
2026-07-11T15:19:23.3498442Z Upgrading pip...
2026-07-11T15:19:25.6164634Z Looking in links: /tmp/tmphybqj02_
2026-07-11T15:19:25.6170404Z Requirement already satisfied: setuptools in /opt/hostedtoolcache/Python/3.9.25/x64/lib/python3.9/site-packages (79.0.1)
2026-07-11T15:19:25.6175759Z Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.9.25/x64/lib/python3.9/site-packages (23.0.1)
2026-07-11T15:19:26.9167624Z Collecting pip
2026-07-11T15:19:26.9976939Z Downloading pip-26.0.1-py3-none-any.whl (1.8 MB)
2026-07-11T15:19:27.1439101Z ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 12.4 MB/s eta 0:00:00
2026-07-11T15:19:27.1439744Z 
2026-07-11T15:19:27.2134072Z Installing collected packages: pip
2026-07-11T15:19:27.2135104Z Attempting uninstall: pip
2026-07-11T15:19:27.2142535Z Found existing installation: pip 23.0.1
2026-07-11T15:19:27.3941578Z Uninstalling pip-23.0.1:
2026-07-11T15:19:27.4013644Z Successfully uninstalled pip-23.0.1
2026-07-11T15:19:28.2418526Z Successfully installed pip-26.0.1
2026-07-11T15:19:28.3020920Z Create complete file
2026-07-11T15:19:28.3068355Z Successfully set up CPython (3.9.25)
2026-07-11T15:19:28.3069254Z ##[endgroup]
2026-07-11T15:19:28.3228341Z ##[group]Run python -m pip install --upgrade pip
2026-07-11T15:19:28.3228824Z [36;1mpython -m pip install --upgrade pip[0m
2026-07-11T15:19:28.3229183Z [36;1mpip install pandas openpyxl msal requests[0m
2026-07-11T15:19:28.3391740Z shell: /usr/bin/bash -e {0}
2026-07-11T15:19:28.3392062Z env:
2026-07-11T15:19:28.3392347Z   pythonLocation: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:28.3392800Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib/pkgconfig
2026-07-11T15:19:28.3393234Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:28.3393621Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:28.3394003Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:28.3394383Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib
2026-07-11T15:19:28.3394709Z ##[endgroup]
2026-07-11T15:19:28.6686992Z Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.9.25/x64/lib/python3.9/site-packages (26.0.1)
2026-07-11T15:19:29.5653971Z Collecting pandas
2026-07-11T15:19:29.6440576Z   Downloading pandas-2.3.3-cp39-cp39-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (91 kB)
2026-07-11T15:19:29.7325802Z Collecting openpyxl
2026-07-11T15:19:29.7528639Z   Downloading openpyxl-3.1.5-py2.py3-none-any.whl.metadata (2.5 kB)
2026-07-11T15:19:29.7938716Z Collecting msal
2026-07-11T15:19:29.8142734Z   Downloading msal-1.37.0-py3-none-any.whl.metadata (11 kB)
2026-07-11T15:19:29.8635849Z Collecting requests
2026-07-11T15:19:29.8839349Z   Downloading requests-2.32.5-py3-none-any.whl.metadata (4.9 kB)
2026-07-11T15:19:30.1854041Z Collecting numpy>=1.22.4 (from pandas)
2026-07-11T15:19:30.2059708Z   Downloading numpy-2.0.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (60 kB)
2026-07-11T15:19:30.2416479Z Collecting python-dateutil>=2.8.2 (from pandas)
2026-07-11T15:19:30.2618406Z   Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
2026-07-11T15:19:30.3203981Z Collecting pytz>=2020.1 (from pandas)
2026-07-11T15:19:30.3409356Z   Downloading pytz-2026.2-py2.py3-none-any.whl.metadata (22 kB)
2026-07-11T15:19:30.3740521Z Collecting tzdata>=2022.7 (from pandas)
2026-07-11T15:19:30.3941519Z   Downloading tzdata-2026.3-py2.py3-none-any.whl.metadata (1.4 kB)
2026-07-11T15:19:30.4220615Z Collecting et-xmlfile (from openpyxl)
2026-07-11T15:19:30.4422908Z   Downloading et_xmlfile-2.0.0-py3-none-any.whl.metadata (2.7 kB)
2026-07-11T15:19:30.4911093Z Collecting PyJWT<3,>=1.0.0 (from PyJWT[crypto]<3,>=1.0.0->msal)
2026-07-11T15:19:30.5117281Z   Downloading pyjwt-2.13.0-py3-none-any.whl.metadata (3.4 kB)
2026-07-11T15:19:30.8099741Z Collecting cryptography<51,>=2.5 (from msal)
2026-07-11T15:19:30.8307123Z   Downloading cryptography-49.0.0-cp39-abi3-manylinux_2_34_x86_64.whl.metadata (4.3 kB)
2026-07-11T15:19:30.9793031Z Collecting charset_normalizer<4,>=2 (from requests)
2026-07-11T15:19:31.0002007Z   Downloading charset_normalizer-3.4.9-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (41 kB)
2026-07-11T15:19:31.0357006Z Collecting idna<4,>=2.5 (from requests)
2026-07-11T15:19:31.0561757Z   Downloading idna-3.18-py3-none-any.whl.metadata (6.1 kB)
2026-07-11T15:19:31.1024970Z Collecting urllib3<3,>=1.21.1 (from requests)
2026-07-11T15:19:31.1229519Z   Downloading urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
2026-07-11T15:19:31.1634870Z Collecting certifi>=2017.4.17 (from requests)
2026-07-11T15:19:31.1839183Z   Downloading certifi-2026.6.17-py3-none-any.whl.metadata (2.5 kB)
2026-07-11T15:19:31.3701496Z Collecting cffi>=2.0.0 (from cryptography<51,>=2.5->msal)
2026-07-11T15:19:31.3908094Z   Downloading cffi-2.0.0-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
2026-07-11T15:19:31.4288194Z Collecting typing-extensions>=4.13.2 (from cryptography<51,>=2.5->msal)
2026-07-11T15:19:31.4494427Z   Downloading typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
2026-07-11T15:19:31.5063519Z Collecting pycparser (from cffi>=2.0.0->cryptography<51,>=2.5->msal)
2026-07-11T15:19:31.5266461Z   Downloading pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
2026-07-11T15:19:31.5586796Z Collecting six>=1.5 (from python-dateutil>=2.8.2->pandas)
2026-07-11T15:19:31.5799522Z   Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
2026-07-11T15:19:31.6073275Z Downloading pandas-2.3.3-cp39-cp39-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (12.8 MB)
2026-07-11T15:19:31.8327143Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.8/12.8 MB 67.3 MB/s  0:00:00
2026-07-11T15:19:31.8536440Z Downloading openpyxl-3.1.5-py2.py3-none-any.whl (250 kB)
2026-07-11T15:19:31.8770107Z Downloading msal-1.37.0-py3-none-any.whl (123 kB)
2026-07-11T15:19:31.9003395Z Downloading requests-2.32.5-py3-none-any.whl (64 kB)
2026-07-11T15:19:31.9235256Z Downloading charset_normalizer-3.4.9-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (214 kB)
2026-07-11T15:19:31.9473231Z Downloading cryptography-49.0.0-cp39-abi3-manylinux_2_34_x86_64.whl (4.7 MB)
2026-07-11T15:19:31.9635627Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.7/4.7 MB 340.0 MB/s  0:00:00
2026-07-11T15:19:31.9839258Z Downloading idna-3.18-py3-none-any.whl (65 kB)
2026-07-11T15:19:32.0077495Z Downloading pyjwt-2.13.0-py3-none-any.whl (31 kB)
2026-07-11T15:19:32.0306008Z Downloading urllib3-2.6.3-py3-none-any.whl (131 kB)
2026-07-11T15:19:32.0538771Z Downloading certifi-2026.6.17-py3-none-any.whl (133 kB)
2026-07-11T15:19:32.0773979Z Downloading cffi-2.0.0-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (216 kB)
2026-07-11T15:19:32.1035095Z Downloading numpy-2.0.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (19.5 MB)
2026-07-11T15:19:32.1830522Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 19.5/19.5 MB 254.0 MB/s  0:00:00
2026-07-11T15:19:32.2046991Z Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
2026-07-11T15:19:32.2283091Z Downloading pytz-2026.2-py2.py3-none-any.whl (510 kB)
2026-07-11T15:19:32.2521567Z Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
2026-07-11T15:19:32.2751360Z Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
2026-07-11T15:19:32.4574587Z Downloading tzdata-2026.3-py2.py3-none-any.whl (348 kB)
2026-07-11T15:19:32.4811014Z Downloading et_xmlfile-2.0.0-py3-none-any.whl (18 kB)
2026-07-11T15:19:32.5038489Z Downloading pycparser-2.23-py3-none-any.whl (118 kB)
2026-07-11T15:19:32.6572608Z Installing collected packages: pytz, urllib3, tzdata, typing-extensions, six, pycparser, numpy, idna, et-xmlfile, charset_normalizer, certifi, requests, python-dateutil, PyJWT, openpyxl, cffi, pandas, cryptography, msal
2026-07-11T15:19:39.8959069Z 
2026-07-11T15:19:39.9001329Z Successfully installed PyJWT-2.13.0 certifi-2026.6.17 cffi-2.0.0 charset_normalizer-3.4.9 cryptography-49.0.0 et-xmlfile-2.0.0 idna-3.18 msal-1.37.0 numpy-2.0.2 openpyxl-3.1.5 pandas-2.3.3 pycparser-2.23 python-dateutil-2.9.0.post0 pytz-2026.2 requests-2.32.5 six-1.17.0 typing-extensions-4.16.0 tzdata-2026.3 urllib3-2.6.3
2026-07-11T15:19:40.1177685Z ##[group]Run python extract_data.py
2026-07-11T15:19:40.1178028Z [36;1mpython extract_data.py[0m
2026-07-11T15:19:40.1210763Z shell: /usr/bin/bash -e {0}
2026-07-11T15:19:40.1211018Z env:
2026-07-11T15:19:40.1211278Z   pythonLocation: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:40.1211712Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib/pkgconfig
2026-07-11T15:19:40.1212129Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:40.1212517Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:40.1212893Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:40.1213265Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib
2026-07-11T15:19:40.1213711Z   TENANT_ID: ***
2026-07-11T15:19:40.1213954Z   CLIENT_ID: ***
2026-07-11T15:19:40.1214252Z   CLIENT_SECRET: ***
2026-07-11T15:19:40.1214473Z ##[endgroup]
2026-07-11T15:19:51.6850007Z Lỗi upload: 400 - {"error":{"code":"BadRequest","message":"/me request is only valid with delegated authentication flow.","innerError":{"date":"2026-07-11T15:19:51","request-id":"f6fd0845-0b43-40f8-9328-baf6f5a6f92e","client-request-id":"f6fd0845-0b43-40f8-9328-baf6f5a6f92e"}}}
2026-07-11T15:19:51.8952016Z ##[group]Run git config --global user.name 'github-actions[bot]'
2026-07-11T15:19:51.8952526Z [36;1mgit config --global user.name 'github-actions[bot]'[0m
2026-07-11T15:19:51.8953037Z [36;1mgit config --global user.email 'github-actions[bot]@users.noreply.github.com'[0m
2026-07-11T15:19:51.8953532Z [36;1m# Chỉ commit nếu file tồn tại[0m
2026-07-11T15:19:51.8953820Z [36;1mif [ -f "output.csv" ]; then[0m
2026-07-11T15:19:51.8954091Z [36;1m  git add output.csv[0m
2026-07-11T15:19:51.8954429Z [36;1m  git commit -m "Auto-generate output.csv from DMS_Input.xlsx"[0m
2026-07-11T15:19:51.8954789Z [36;1m  git push[0m
2026-07-11T15:19:51.8954997Z [36;1melse[0m
2026-07-11T15:19:51.8955268Z [36;1m  echo "output.csv không tìm thấy, bỏ qua commit."[0m
2026-07-11T15:19:51.8955757Z [36;1mfi[0m
2026-07-11T15:19:51.8987807Z shell: /usr/bin/bash -e {0}
2026-07-11T15:19:51.8988062Z env:
2026-07-11T15:19:51.8988340Z   pythonLocation: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:51.8988818Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib/pkgconfig
2026-07-11T15:19:51.8989259Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:51.8989644Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:51.8990171Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.9.25/x64
2026-07-11T15:19:51.8990563Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.9.25/x64/lib
2026-07-11T15:19:51.8990892Z ##[endgroup]
2026-07-11T15:19:51.9075375Z output.csv không tìm thấy, bỏ qua commit.
2026-07-11T15:19:51.9166112Z Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
2026-07-11T15:19:51.9167385Z Post job cleanup.
2026-07-11T15:19:52.0376215Z (node:2574) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
2026-07-11T15:19:52.0377046Z (Use `node --trace-deprecation ...` to show where the warning was created)
2026-07-11T15:19:52.0567326Z Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
2026-07-11T15:19:52.0568582Z Post job cleanup.
2026-07-11T15:19:52.1498666Z [command]/usr/bin/git version
2026-07-11T15:19:52.1545196Z git version 2.54.0
2026-07-11T15:19:52.1616491Z Copying '/home/runner/.gitconfig' to '/home/runner/work/_temp/fa1c1820-e1ef-42f0-ba29-d5ce0d1c3d06/.gitconfig'
2026-07-11T15:19:52.1627900Z Temporarily overriding HOME='/home/runner/work/_temp/fa1c1820-e1ef-42f0-ba29-d5ce0d1c3d06' before making global git config changes
2026-07-11T15:19:52.1630512Z Adding repository directory to the temporary git global config as a safe directory
2026-07-11T15:19:52.1634291Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/AutoDMS/AutoDMS
2026-07-11T15:19:52.1678809Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-07-11T15:19:52.1728795Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-07-11T15:19:52.1985228Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-07-11T15:19:52.2017560Z http.https://github.com/.extraheader
2026-07-11T15:19:52.2032377Z [command]/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
2026-07-11T15:19:52.2083913Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-07-11T15:19:52.2381352Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-07-11T15:19:52.2389997Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-07-11T15:19:52.2817183Z Cleaning up orphan processes
2026-07-11T15:19:52.3224415Z ##[warning]Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
