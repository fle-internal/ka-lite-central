# This is an adapted version of KA Lite 0.16's "make assets" target
# because a step fails now and we don't want to re-release it.

npm cache clean
npm install --production
node build.js
bin/kalite manage compileymltojson
bin/kalite manage syncdb --noinput
bin/kalite manage migrate
mkdir -p kalite/database/templates/
cp kalite/database/data.sqlite kalite/database/templates/

# This is the replaced step: Before we were just doing
# "retrievecontentpack download" but it fails with an error that got fixed in
# 0.17
wget -c -O en-minimal.zip http://pantry.learningequality.org/downloads/ka-lite/0.16/content/contentpacks/en-minimal.zip
bin/kalite manage retrievecontentpack local en en-minimal.zip --foreground --template
