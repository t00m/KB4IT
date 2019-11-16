echo "Checking coding standard for file: $1"
echo "================================================================="
pylint $1
echo ""
echo "Checking code style for file: $1"
echo "================================================================="
pycodestyle --max-line-length=100 --show-source --statistics $1
echo ""
echo "Checking doc style for file: $1"
echo "================================================================="
pydocstyle $1
