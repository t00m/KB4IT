echo "Checking coding standard for file: $1"
echo "================================================================="
pylint -d C0301 $1
echo ""
#~ echo "Checking code style for file: $1"
#~ echo "================================================================="
#~ pycodestyle --ignore E501--max-line-length=100 --show-source --statistics $1
#~ echo ""
#~ echo "Checking doc style for file: $1"
#~ echo "================================================================="
#~ pydocstyle $1
