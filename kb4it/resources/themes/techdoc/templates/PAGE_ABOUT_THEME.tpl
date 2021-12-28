= About theme ${var['theme']['name']}

[options="header", width="100%", cols="20%,80%"]
|===
| *Key*
| *Value*
% for key in var['theme']:

| *${key}*
| `${var['theme'][key]}`
% endfor
|===


