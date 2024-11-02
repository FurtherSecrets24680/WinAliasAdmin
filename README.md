# WinAliasAdmin
**WinAliasAdmin** is a tool for Windows power users that can be used to create, edit, and delete custom app execution aliases directly in the registry through an intuitive interface. These aliases can be used to run any app from **"Run" / "Win + R"** in Windows.

# Interface
<img src="https://github.com/FurtherSecrets24680/WinAliasAdmin/blob/main/demo.png" width="800" height="550">

**Example**: I've added c.exe as a custom alias to run command prompt more quickly throught the "Run" dialog, which isn't by default.

# Notes
- This tool always runs with administrative previleges, as you can see in the manifest file which is automatically generated. It uses powershell to check that manifest to run this software as admin.
- The admin previleges are required to edit the Windows registry, where these app execution aliases are located.
- You can already enable/disable existing aliases very easily by going to **Settings > Apps> Advanced App Settings > App Execution Aliases** (Windows 11), and also edit or delete them in the registry editor. But this tool can be used to edit, create or delete app execution aliases easily, without using the registry editor. This is preferred as you won't be able to delete any important registry key by mistake.
