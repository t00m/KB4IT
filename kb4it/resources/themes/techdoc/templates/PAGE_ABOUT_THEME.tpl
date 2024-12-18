= About theme ${var['theme']['name']}

:SystemPage:    Yes
:Updated:       2024-08-26 12:00:00

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


