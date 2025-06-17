# SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
#
# SPDX-License-Identifier: MIT

echo -n "Build current minimized bootstrap.min.css ... "
docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > bootstrap.min.css  2>/dev/null

exit_code=$?

if [ $exit_code -eq 126 ]; then
  echo -n '\nRe-running docker with sudo prefix ... '
  sudo docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > bootstrap.min.css  2>/dev/null
  exit_code=$?
fi

if [ $exit_code -eq 0 ]; then
  echo "done and successful.\n"
  echo -n "Checking diff ... "
  sed 's/\([;}]\)/\1\n/g' bootstrap.min.css > check_new.css
  sed 's/\([;}]\)/\1\n/g' ../base/static/css/bootstrap.min.css > check_old.css

  echo "the diff between the current bootstrap.min.css and the newly compressed file is:\n"
  diff check_old.css check_new.css

  echo "\nFound `(diff  -y --suppress-common-lines check_old.css check_new.css | wc -l)` change(s)\n"
  rm  -f check_new.css check_old.css

  echo "If this diff is fine for you, copy the bootstrap.min.css to ../base/static/css/bootstrap.min.css, e.g."
  echo "mv bootstrap.min.css ../base/static/css/bootstrap.min.css"
else
  echo "failed.\n"
  echo "Please check the output of"
  echo "docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > bootstrap.min.css"
fi
