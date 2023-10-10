# Tungsten
Small programming language designed to work with Hackasm and VM-O-MATIC
```
# work in progress...
# Using assembly because the language still lacks many features
# All of this will soon be possible with high level syntax
fn add_8_8(a byte, b byte) byte {
  asm "ldrx %a";        # Loads X with 1-byte value from the address of `a`
  asm "ldry %b";        # Loads Y with 1-byte value from the address of `b`
  asm "addxy";          # Adds X and Y together
  asm "strx %__ret";    # Saves the result in the return buffer
  noret;                # Signals that the function returns a value even if there's no `ret`
}

fn main void {
  buf x byte;         # Declaration
  buf y byte;         # Declaration
  buf z byte;         # Declaration

  x = 1;              # Assignment: NOT SUPPORTED YET
  y = 2;              # Assignment: NOT SUPPORTED YET
  z = add_8_8(x, y);  # Assignment with call: NOT SUPPORTED YET (Expr evaluation)
}
```
