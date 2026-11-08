<!DOCTYPE html>
<html lang="${var['lang']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${var['page']['title']} | ${var['repo']['title']}</title>
    <link rel="stylesheet" href="resources/themes/starter-plain/framework/style.css">
</head>
<body>
<header>
    <a href="index.html">${var['repo']['title']}</a>
    ${var['search_box'] | n}
</header>
