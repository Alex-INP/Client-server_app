import dis


class ServerMetaclass(type):
    """
    Метакласс следит за наличием необходимых функций в серверном классе.
    """
    def __init__(self, clsname, bases, clsdict):
        methods = []
        attrs = []

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == "LOAD_ATTR":
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        print(f"{methods=}")
        print(f"{attrs=}")
        if "connect" in methods:
            raise TypeError(
                "You cannot use 'connect' method in server class instance")

        if not ("SOCK_STREAM" in methods and "AF_INET" in methods):
            raise TypeError("Socket initialisation incorrect")

        super().__init__(clsname, bases, clsdict)


class ClientMetaclass(type):
    """
    Метакласс следит за наличием необходимых функций в клиентском классе.
    """
    def __init__(self, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in ("accept", "listen"):
            if command in methods:
                raise TypeError(f"Forbidden method in class {command}")

        if "get_message" in methods or "send_message" in methods:
            pass
        else:
            raise TypeError("No socket communication-vital function calls.")

        super().__init__(clsname, bases, clsdict)


class DocstringMetaclass(type):
    """
    Метакласс следит за наличием строк документации в классах.
    """
    def __init__(self, clsname, bases, clsdict):
        if "__doc__" not in clsdict.keys():
            raise TypeError(
                f"Class '{clsname}' must have a documentation string.")

        no_dockstring_funcs = []
        for key, val in clsdict.items():
            if key[:2] != "__" and hasattr(
                    val, "__call__") and not getattr(val, "__doc__"):
                no_dockstring_funcs.append(key)

        if no_dockstring_funcs:
            raise TypeError(
                f"Functions in class '{clsname}' must have a documentation string. Functions without documentation string: {no_dockstring_funcs}")

        super().__init__(clsname, bases, clsdict)
