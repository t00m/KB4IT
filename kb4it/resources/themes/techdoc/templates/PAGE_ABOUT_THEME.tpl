= About theme ${var['theme']['name']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

[options="header", width="100%", cols="20%,80%"]
|===
| *Key*
| *Value*
% for key in var['theme']:

| *${key}*
| `${var['theme'][key]}`
% endfor
|===


