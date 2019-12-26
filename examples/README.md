# Usage examples

This page will show some use cases of the SWIFI tool. The tool will perform modifications on an executable. The executable is built from this C code computing the greatest common divisor of two number :
```c
int gcd(int a, int b)
{
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```
The compilation is done with `gcc -o gcd gcd.c` and the we can inspect the assembly with `objdump -d gcd` :
<pre>
...
00000000000005fa &lt;gcd&gt;:
 5fa:   55                      push   %rbp
 5fb:   48 89 e5                mov    %rsp,%rbp
 5fe:   48 83 ec 10             sub    $0x10,%rsp
 602:   89 7d fc                mov    %edi,-0x4(%rbp)
 605:   89 75 f8                mov    %esi,-0x8(%rbp)
 608:   83 7d f8 00             cmpl   $0x0,-0x8(%rbp)
 60c:   75 05                   jne    613 &lt;gcd+0x19&gt;
 60e:   8b 45 fc                mov    -0x4(%rbp),%eax
 611:   eb 13                   jmp    626 &lt;gcd+0x2c&gt;
 613:   8b 45 fc                mov    -0x4(%rbp),%eax
 616:   99                      cltd   
 617:   f7 7d f8                idivl  -0x8(%rbp)
 61a:   8b 45 f8                mov    -0x8(%rbp),%eax
 61d:   89 d6                   mov    %edx,%esi
 61f:   89 c7                   mov    %eax,%edi
 621:   e8 d4 ff ff ff          callq  5fa &lt;gcd&gt;
 626:   c9                      leaveq
 627:   c3                      retq   
...
</pre>

## NOP some instructions

To NOP instructions, we only need to specify the range and the architecture.

```
python3 ../swifitool/faults_inject.py -i gcd -o gcd_nop -a x86 NOP 0x617-0x619
```
Here we decided to nop entirely the `idivl` instruction.
<pre>
...
00000000000005fa &lt;gcd&gt;:
 5fa:   55                      push   %rbp
 5fb:   48 89 e5                mov    %rsp,%rbp
 5fe:   48 83 ec 10             sub    $0x10,%rsp
 602:   89 7d fc                mov    %edi,-0x4(%rbp)
 605:   89 75 f8                mov    %esi,-0x8(%rbp)
 608:   83 7d f8 00             cmpl   $0x0,-0x8(%rbp)
 60c:   75 05                   jne    613 &lt;gcd+0x19&gt;
 60e:   8b 45 fc                mov    -0x4(%rbp),%eax
 611:   eb 13                   jmp    626 &lt;gcd+0x2c&gt;
 613:   8b 45 fc                mov    -0x4(%rbp),%eax
 616:   99                      cltd   
<b> 617:   90                      nop
 618:   90                      nop
 619:   90                      nop</b>
 61a:   8b 45 f8                mov    -0x8(%rbp),%eax
 61d:   89 d6                   mov    %edx,%esi
 61f:   89 c7                   mov    %eax,%edi
 621:   e8 d4 ff ff ff          callq  5fa &lt;gcd&gt;
 626:   c9                      leaveq
 627:   c3                      retq
...
</pre>
On x86 executables if the range is not aligned with the previous instructions, the remaining part of the instrution (and the next ones) will be decoded differently and change entirely the behavior of the program.

## Zero bytes (or words)

It's also possible to set to 0 some bytes (or words) of the binary.
```
python3 ../swifitool/faults_inject.py -i gcd -o gcd_zero -w 2 Z1B 0x626 Z1W 0x61f
```
In this case, it will break the decoding of the subsequent instructions.
<pre>
...
00000000000005fa &lt;gcd&gt;:
 5fa:   55                      push   %rbp
 5fb:   48 89 e5                mov    %rsp,%rbp
 5fe:   48 83 ec 10             sub    $0x10,%rsp
 602:   89 7d fc                mov    %edi,-0x4(%rbp)
 605:   89 75 f8                mov    %esi,-0x8(%rbp)
 608:   83 7d f8 00             cmpl   $0x0,-0x8(%rbp)
 60c:   75 05                   jne    613 &lt;gcd+0x19&gt;
 60e:   8b 45 fc                mov    -0x4(%rbp),%eax
 611:   eb 13                   jmp    626 &lt;gcd+0x2c&gt;
 613:   8b 45 fc                mov    -0x4(%rbp),%eax
 616:   99                      cltd   
 617:   f7 7d f8                idivl  -0x8(%rbp)
 61a:   8b 45 f8                mov    -0x8(%rbp),%eax
 61d:   89 d6                   mov    %edx,%esi
<b> 61f:   00 00                   add    %al,(%rax)</b>
 621:   e8 d4 ff ff ff          callq  5fa &lt;gcd&gt;
<b> 626:   00 c3                   add    %al,%bl</b>
...
</pre>

## Flip some bits in the binary
Flipping one bit can have a lot of different consequences.
```
python3 ../swifitool/faults_inject.py -i gcd -o gcd_flip FLP 0x610 5
```
In this case, the accessed offset on the stack is changed.
<pre>
...
00000000000005fa &lt;gcd&gt;:
 5fa:   55                      push   %rbp
 5fb:   48 89 e5                mov    %rsp,%rbp
 5fe:   48 83 ec 10             sub    $0x10,%rsp
 602:   89 7d fc                mov    %edi,-0x4(%rbp)
 605:   89 75 f8                mov    %esi,-0x8(%rbp)
 608:   83 7d f8 00             cmpl   $0x0,-0x8(%rbp)
 60c:   75 05                   jne    613 &lt;gcd+0x19&gt;
 <b>60e:   8b 45 dc                mov    -0x24(%rbp),%eax</b>
 611:   eb 13                   jmp    626 &lt;gcd+0x2c&gt;
 613:   8b 45 fc                mov    -0x4(%rbp),%eax
 616:   99                      cltd   
 617:   f7 7d f8                idivl  -0x8(%rbp)
 61a:   8b 45 f8                mov    -0x8(%rbp),%eax
 61d:   89 d6                   mov    %edx,%esi
 61f:   89 c7                   mov    %eax,%edi
 621:   e8 d4 ff ff ff          callq  5fa &lt;gcd&gt;
 626:   c9                      leaveq
 627:   c3                      retq   
...
</pre>


## Change the target of a jump instructions
Changing the target of a jump can lead to the execution of dangerous hidden code. 
```
python3 ../swifitool/faults_inject.py -i gcd -o gcd_jmp -a x86 JMP 0x611 0x600 JBE 0x60c 0x600
```
It can also lead to decoding error if the target is not aligned with existing instructions.
<pre>
...
00000000000005fa &lt;gcd&gt;:
 5fa:   55                      push   %rbp
 5fb:   48 89 e5                mov    %rsp,%rbp
 5fe:   48 83 ec 10             sub    $0x10,%rsp
 602:   89 7d fc                mov    %edi,-0x4(%rbp)
 605:   89 75 f8                mov    %esi,-0x8(%rbp)
 608:   83 7d f8 00             cmpl   $0x0,-0x8(%rbp)
 <b>60c:   75 f2                   jne    600 &lt;gcd+0x6&gt;</b>
 60e:   8b 45 fc                mov    -0x4(%rbp),%eax
 <b>611:   eb ed                   jmp    600 &lt;gcd+0x6&gt;</b>
 613:   8b 45 fc                mov    -0x4(%rbp),%eax
 616:   99                      cltd   
 617:   f7 7d f8                idivl  -0x8(%rbp)
 61a:   8b 45 f8                mov    -0x8(%rbp),%eax
 61d:   89 d6                   mov    %edx,%esi
 61f:   89 c7                   mov    %eax,%edi
 621:   e8 d4 ff ff ff          callq  5fa &lt;gcd&gt;
 626:   c9                      leaveq
 627:   c3                      retq   
...
</pre>

# On ARM

All the previous fault models also work on ARM executables. For the jump fault model, the target of the B (or BL) instruction is changed. 
Thumb instructions are not currently supported.
