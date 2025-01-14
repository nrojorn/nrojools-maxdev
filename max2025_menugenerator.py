import os
import uuid
from pymxs import runtime as rt

class MenuGenerator:
    """
    A generic class to generate menus in 3ds Max based on a directory structure.
    """
    def __init__(
        self,
        root_directory_path,
        main_menu_name="Tools Menu",
        quad_menu_name="Tools Quad Menu",
        quad_menu_modifier_keys="CTRL+SHIFT",
        quad_menu_position="TOP_RIGHT",
        print_tree=False
    ):
        """
        Initializes the MenuGenerator.

        Args:
            root_directory_path (str): The path to the root directory whose structure will be used to create the menus.
            main_menu_name (str, optional): The name of the main menu. Defaults to "Tools Menu".
            quad_menu_name (str, optional): The name of the quad menu. Defaults to "Tools Quad Menu".
            quad_menu_modifier_keys (str, optional): The modifier keys required for the quad menu. Defaults to "CTRL+SHIFT".
            quad_menu_position (str, optional): The position of the quad menu. Defaults to "TOP_RIGHT".
            print_tree (bool, optional): Whether to print the directory tree structure. Defaults to False.
        """
        self.root_directory_path = root_directory_path
        self.main_menu_name = main_menu_name
        self.quad_menu_name = quad_menu_name
        self.quad_menu_modifier_keys = quad_menu_modifier_keys
        self.quad_menu_position = quad_menu_position
        self.print_tree = print_tree
        self.directory_tree = self._build_tree(self.root_directory_path, is_root=True)

    # Build an in-memory tree so we only traverse the filesystem once.
    # =======================================================
    def _build_tree(self, path, is_root=False):
        node_name = os.path.basename(path.rstrip("\\/"))
        if not node_name:
            node_name = os.path.basename(path)
        node = {
            "name": node_name if not is_root else node_name,
            "path": path,
            "type": "directory" if os.path.isdir(path) else "file",
            "children": [],
        }
        if os.path.isdir(path):
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                node["children"].append(self._build_tree(item_path, is_root=False))
        return node

    # Optional ASCII printing of that tree.
    # =======================================================
    def _print_directory_tree(self, node, prefix="", is_last=True, is_root=False):
        connector = "└── " if is_last else "├── "
        if not is_root:
            print(prefix + connector + node["name"])
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node["children"]):
            last_child = (i == len(node["children"]) - 1)
            self._print_directory_tree(child, prefix=child_prefix, is_last=last_child, is_root=False)

    # Read macro info from .mcr files.
    # =======================================================
    def read_macro_file(self, input_path, macro_start_identifier="macroScript", category_identifier="category:"):
        """
        Reads macro name and category from a macro file.

        Args:
            input_path (str): The path to the macro file.
            macro_start_identifier (str, optional): The string that indicates the start of the macro name definition. Defaults to "macroScript".
            category_identifier (str, optional): The string that indicates the start of the category definition. Defaults to "category:".

        Returns:
            tuple: A tuple containing the macro name and category, or empty strings if not found.
        """
        macro_name, macro_category = "", ""
        if not os.path.isfile(input_path):
            return macro_name, macro_category
        with open(input_path, "r") as macro_file:
            lines = [line.strip() for line in macro_file if not line.strip().startswith("--")]
        for line in lines:
            if macro_start_identifier in line and not macro_name:
                macro_name = line.split()[1]
            if category_identifier in line and not macro_category:
                parts = line.split('"')
                if len(parts) >= 2:
                    macro_category = parts[1]
            if macro_name and macro_category:
                break
        return macro_name, macro_category

    # Create menus from the in-memory tree.
    # =======================================================
    def _create_menu_from_tree(self, parent_menu, node):
        if os.path.normpath(node["path"]) == os.path.normpath(self.root_directory_path):
            current_menu = parent_menu
        else:
            if node["type"] == "directory":
                current_menu = parent_menu.createSubMenu(str(uuid.uuid4()), node["name"])
            else:
                return
        for child in node["children"]:
            if child["type"] == "file" and child["path"].lower().endswith(".mcr"):
                macro_name, macro_category = self.read_macro_file(child["path"])
                if macro_name and macro_category:
                    current_menu.createAction(str(uuid.uuid4()), 647394, f"{macro_name}`{macro_category}")
        for child in node["children"]:
            if child["type"] == "directory":
                self._create_menu_from_tree(current_menu, child)

    # Create the main 3ds Max menu.
    # =======================================================
    def define_main_menu(self):
        menu_mgr = rt.callbacks.notificationParam()
        main_menu_bar = menu_mgr.mainMenuBar
        menu = main_menu_bar.createSubMenu(str(uuid.uuid4()), self.main_menu_name)
        if self.print_tree:
            children = self.directory_tree["children"]
            for i, child in enumerate(children):
                last_child = (i == len(children) - 1)
                self._print_directory_tree(child, is_last=last_child, is_root=False)
            print()
            self.print_tree = False

        self._create_menu_from_tree(menu, self.directory_tree)

    # Create the quad menu.
    # =======================================================
    def define_quad_menu(self):
        quad_menu_mgr = rt.callbacks.notificationParam()
        viewport_context_id = "ac7c70f8-3f86-4ff5-a510-e4fd6a9c368e"
        viewport_context = quad_menu_mgr.GetContextById(viewport_context_id)
        quad_menu = viewport_context.CreateQuadMenu(str(uuid.uuid4()), self.quad_menu_name)

        modifier_keys_map = {
            "NONE": "nonePressed",
            "ALT": "altPressed",
            "CTRL": "controlPressed",
            "CTRL+ALT": "controlAndAltPressed",
            "CTRL+SHIFT": "shiftAndControlPressed",
            "SHIFT+ALT+CTRL": "shiftAndAltAndControlPressed",
            "SHIFT": "shiftPressed",
            "SHIFT+ALT": "shiftAndAltPressed",
        }
        rt.name(self.quad_menu_modifier_keys)
        if self.quad_menu_modifier_keys in modifier_keys_map:
            rt.name(modifier_keys_map[self.quad_menu_modifier_keys])
            viewport_context.SetRightClickModifiers(quad_menu, rt.name(modifier_keys_map[self.quad_menu_modifier_keys]))
        else:
            print(f"Warning: Invalid modifier key combination '{self.quad_menu_modifier_keys}'. Using default.")

        quad_menu_positions = {
            "TOP_LEFT": "TopLeft",
            "TOP_RIGHT": "TopRight",
            "BOTTOM_RIGHT": "BottomRight",
            "BOTTOM_LEFT": "BottomLeft",
        }
        if self.quad_menu_position in quad_menu_positions:
            position = quad_menu_positions[self.quad_menu_position]
            menu = quad_menu.CreateMenu(str(uuid.uuid4()), position, rt.name(position))
            self._create_menu_from_tree(menu, self.directory_tree)
        else:
            print(f"Warning: Invalid quad menu position '{self.quad_menu_position}'. Using default 'TOP_RIGHT'.")
            position = quad_menu_positions["TOP_RIGHT"]
            menu = quad_menu.CreateMenu(str(uuid.uuid4()), position, rt.name(position))
            self._create_menu_from_tree(menu, self.directory_tree)

    # Register both menus with 3ds Max, then reload UI config.
    # =======================================================
    def register_menus(self, main_menu_callback_id="menu_callback", quad_menu_callback_id="quad_menu_callback"):
        """
        Registers the defined main and quad menus with 3ds Max.

        Args:
            main_menu_callback_id (str, optional): The callback ID for the main menu. Defaults to "menu_callback".
            quad_menu_callback_id (str, optional): The callback ID for the quad menu. Defaults to "quad_menu_callback".
        """
        rt.callbacks.removeScripts(id=rt.name(main_menu_callback_id))
        rt.callbacks.addScript(rt.name("cuiRegisterMenus"), self.define_main_menu, id=rt.name(main_menu_callback_id))
        rt.callbacks.removeScripts(id=rt.name(quad_menu_callback_id))
        rt.callbacks.addScript(rt.name("cuiRegisterQuadMenus"), self.define_quad_menu, id=rt.name(quad_menu_callback_id))
        iCuiMenuMgr = rt.maxOps.GetICuiMenuMgr()
        iCuiMenuMgr.LoadConfiguration(iCuiMenuMgr.GetCurrentConfiguration())
        iCuiQuadMenuMgr = rt.maxOps.GetICuiQuadMenuMgr()
        iCuiQuadMenuMgr.LoadConfiguration(iCuiQuadMenuMgr.GetCurrentConfiguration())

# Example Usage
# =======================================================
if __name__ == "__main__":
    # Define the root directory for the menu
    tools_directory = os.path.join(rt.getDir(rt.name("userMacros")), "Jorn Tools")
    tools_directory = rt.getDir(rt.name("userMacros"))

    # Create an instance of the MenuGenerator with custom settings
    menu_generator = MenuGenerator(
        root_directory_path=tools_directory,
        main_menu_name="Custom Tools",
        quad_menu_name="Custom Tools Quad",
        quad_menu_modifier_keys="ALT",
        quad_menu_position="BOTTOM_LEFT",
        print_tree=True
    )

    # Register the menus
    menu_generator.register_menus(main_menu_callback_id="custom_menu", quad_menu_callback_id="custom_quad_menu")
