# ObjectDisorient

An Object Disoriented intepreter.

Object Disoriented is an esoteric language. Its specification is at <https://esolangs.org/wiki/Object_disoriented>.

## instructions

### statements
| code  | meaning |
| ---   | --- |
| `c**` | copy object 1 to object 2 |
| `o*`  | output object |
| `*`   | expression statement |
| `r*`  | return from function |

### l-values
| code | meaning |
| ---  | --- |
| `a`  | member data `a` |
| `b`  | member data `b` |
| `s`  | self |
| `t`  | function local variable |
| `p`  | function parameter |

### r-values
| code     | meaning |
| ---      | --- |
| `z`      | zero object |
| `f**`    | use function of object 1 on object 2 |
| `n(f)**` | new object with code (f) and member data \* and \* |
| `l"id".` | return a new instance of class "id" |
| `i`      | input one bit |

### definitions
| code          | meaning |
| ---           | --- |
| `d"id".(f)**` | define class with name "id", code (f), and member data \* and \* |
| `dmain.(f)**` | define entry point |
| `ecomment.`   | this is a comment |
