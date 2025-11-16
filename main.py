import argparse
import glob
import os
import requests
import sys
import time
import util
from contextlib import ExitStack
from pathlib import Path


def main(project: str, version: str, path_input: str, api_key: str) -> None:
	backup_url = f"https://api.wurstclient.net/artifact-backups/{project}/{version}"
	headers = {
		"X-API-Key": api_key,
		"Accept": "application/json",
	}

	retry_count = 0
	max_retries = 3
	success = False

	file_paths = _parse_path(path_input)

	while not success and retry_count < max_retries:
		try:
			with ExitStack() as stack:
				files_param = [
					("files", (fp.name, stack.enter_context(open(fp, "rb")))) for fp in file_paths
				]

				# Note: The server usually times out after 100 seconds, this is just a fallback
				response = requests.post(
					backup_url, headers=headers, files=files_param, timeout=120
				)
				if response.status_code != 200:
					raise requests.HTTPError(f"HTTP {response.status_code}: {response.text}")

				success = True
				n_files = len(file_paths)
				util.log(
					f"Successfully uploaded {n_files} file{'' if n_files == 1 else 's'} to {backup_url}"
				)

		except Exception as e:
			retry_count += 1
			if retry_count >= max_retries:
				raise Exception(f"Failed to upload backups after {max_retries} attempts: {e}")

			util.log(f"Upload attempt {retry_count} failed: {e}. Retrying in 5 seconds...")
			time.sleep(5)


def _parse_path(path: str) -> list[Path]:
	files: list[Path] = []
	for pattern in path.splitlines():
		pattern = pattern.strip()
		if not pattern:
			continue

		# Expand glob pattern
		matched_paths = glob.glob(pattern, recursive=True)

		if not matched_paths:
			# If no glob match, check if it's a direct path
			p = Path(pattern)
			if p.exists():
				matched_paths = [pattern]
			else:
				util.gh_error(f"No files matched pattern: {pattern}")
				sys.exit(1)

		for matched_path in matched_paths:
			p = Path(matched_path)
			if p.is_file():
				files.append(p)
			elif p.is_dir():
				# If directory, add all files in it (non-recursive by default)
				files.extend([f for f in p.iterdir() if f.is_file()])

	if not files:
		util.gh_error(f"No files found matching path: {path}")
		sys.exit(1)

	util.log(
		f"Found {len(files)} file{'' if len(files) == 1 else 's'} to upload:{[f.name for f in files]}"
	)
	return files


if __name__ == "__main__":
	try:
		parser = argparse.ArgumentParser(description="Upload artifacts to backup server")
		parser.add_argument("project")
		parser.add_argument("version")
		parser.add_argument("path")
		args = parser.parse_args()

		api_key = os.getenv("WI_BACKUPS_API_KEY")
		if not api_key:
			util.gh_error("API key is missing or empty.")
			sys.exit(1)

		main(
			project=args.project,
			version=args.version,
			path_input=args.path,
			api_key=api_key,
		)
	except Exception as e:
		util.gh_error(e)
		util.gh_traceback()
		sys.exit(1)
