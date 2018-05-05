import os
import shutil
for root, dirs, files in os.walk("."):
	if os.path.basename(root) == 'migrations':
		for file in files:
			path = os.path.abspath(os.path.join(root, file))
			if (os.path.basename(path) != '__init__.py'):
				os.remove(path)
	elif os.path.basename(root) == '__pycache__':
		shutil.rmtree(root)