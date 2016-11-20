import Tkinter
import tkSimpleDialog


class MyDialog(tkSimpleDialog.Dialog):

    def body(self, master):
        Tkinter.Label(master, text="First:").grid(row=0)
        Tkinter.Label(master, text="Private access:").grid(row=1)

        self.e1 = Tkinter.Entry(master)
        v = Tkinter.IntVar()
        self.e2 = Tkinter.Checkbutton(master, variable=v)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        first = int(self.e1.get())
        second = int(self.e2.var)
        print first, second # or something

root = Tkinter.Tk()

d = MyDialog(root)
print d.result