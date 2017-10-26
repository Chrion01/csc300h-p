# Mini C

AST transformer based on PyCParser.

Have a look at the test files for use (needs PyCParser installed).

Setting up your project

Your first task for project one will be simply to set up your project.

Since everyone has choosen Python as their main programming language, I provide a basic tool for the project:

https://github.com/victornicolet/pyminic

You can use the abstract syntax tree defined in minic/minic_ast.py the same way I used the bigger PyCParser AST in the tutorial, and use visitors by extending the NodeVisitor class in the minic_ast.py file. There is nothing different from the tutorial, except that the programming language is more restricted.

You can also have a look at the tests folder.

To start your project, I advise you to include the whole pyminic folder as a subfolder of your project. I might update it if some bugs are encountered, so it is best if you can update it using git.

(if you are familiar with git, use submodules, but don't lose time with this, you can also just copy the folder and update it manually later).

Remark: to use pyminic, you have to install PyCParser first : https://github.com/eliben/pycparser

For the first check-in of the project (due Friday 27/10), I expect you to have a tool that outputs the set of written of each loop body in the program (the inputs are on the projects resources page).You can send me your zipped project folder, or better, share a link to your repository with a control version system (e.g. Git, SVN) that I can view.

