import os
import shutil
folders = ['__pycache__','migrations']
for root, dirs, files in os.walk("."):
	if os.path.basename(root) in folders:
		shutil.rmtree(root)
