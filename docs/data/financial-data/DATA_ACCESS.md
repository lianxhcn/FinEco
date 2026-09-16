# CSMAR 数据获取与校验

更新日期：2026-09-16。

## 下载入口

教师提供的 [CSMAR 2014–2025 数据包 (坚果云)](https://www.jianguoyun.com/p/DWx17VcQtKiFCBivgLEGIAA)。源文件标注仅供中山大学使用；分享链接不改变数据库的使用条件。请在已有课程和数据库授权范围内使用，不向个人公共仓库再分发原始记录或完整派生数据。

本次已检查本地原包；网页检查工具未能读取坚果云分享页，未声称完成云端下载验证。若链接要求登录、失效或没有访问权限，请联系教师。

| 项目 | 本地已核验值 |
|---|---|
| 文件名 | `raw-zip-CSMAR-2014-2025.zip` |
| 字节数 | `104332652` |
| SHA256 | `d493f4218e429c19a1ad33e8311b08cb9b82837148e258972a53f3268c3dc0b9` |
| 内容 | 10 个数据库原始 ZIP 和 1 份数据库说明 PDF |

在 PowerShell 中校验下载文件，路径换成实际保存位置：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:/Downloads/raw-zip-CSMAR-2014-2025.zip'
```

结果应与上表相同。若不同，先核对下载是否完整及教师是否更新了版本，不直接沿用当前审计结果。

## 放置目录

1. 解压外层数据包，得到 `raw-zip-CSMAR-2014-2025/` 文件夹。
2. 将其中 10 个 ZIP 原样复制到授权数据根目录的 `raw-zip/` 子目录。保留中文文件名；此时不要逐个解压内部 ZIP，程序会在运行时处理。说明 PDF 可以留在授权目录供阅读。
3. 检查解压后的中文文件名。若出现乱码，使用支持 ZIP 中文编码的解压工具，以 GBK/CP936 文件名编码重新解压；不要对原始 ZIP 内容做转码。
4. 设置 `FINECO_CSMAR_ROOT` 为授权数据根目录，按 [运行说明](README.md) 执行。

```text
D:/course-private/csmar/
  raw-zip/
    上市公司基本信息年度表213006778(仅供中山大学使用).zip
    ……其余 9 个数据库 ZIP
```

```powershell
$env:FINECO_CSMAR_ROOT = 'D:/course-private/csmar'
(Get-ChildItem -LiteralPath "$env:FINECO_CSMAR_ROOT/raw-zip" -Filter '*.zip').Count
```

计数应为 10。变量指向 `csmar`，不要指向外层 ZIP，也不要指向 `raw-zip` 子目录。原文件名及各包哈希见 [来源清单](SOURCE_MANIFEST.md)。公开仓库只提供代码、规则、说明和汇总输出。
