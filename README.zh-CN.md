# ResearchAuditKit

**简体中文** | [返回英文版](README.md)

**研究文件发生变化时，立即查看哪些研究声明需要重新复核。**

明确列出结果文件，将它们与自己填写的声明关联；文件变化或缺失时，查看需要复核的声明及追溯路径。全部在本地运行，无需执行项目代码、上传文件、调用模型或使用显卡。

**实验性项目 · 候选版本 0.1.0rc4 · GitHub 预发布 · 暂无稳定版本**

[![持续集成](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml/badge.svg)](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/actions/workflows/ci.yml)
[![支持的 Python 版本](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![许可证](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## 安装

以 [GitHub 发布页面](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases)为正式分发依据。先使用随附的 `SHA256SUMS` 核对第四个候选版本的发布文件，再在自己的 Python 环境中安装：

```bash
python -m pip install "https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/download/v0.1.0-rc.4/research_audit_kit-0.1.0rc4-py3-none-any.whl"
rak --version  # rak 0.1.0rc4
```

本项目尚未通过 PyPI 或 TestPyPI 分发。安装过程可能下载 PyYAML；证据检查本身在本地完成。也可以从经过审阅的源码工作目录安装：

```bash
python -m pip install -e .
```

## 第一个项目：列出文件 → 记录基准 → 运行检查

在项目目录中启动引导：

```bash
rak evidence wizard
```

为结果文件填写名称和相对路径。可以选择添加声明，并明确填写支持或反驳该声明的文件名称。预览后确认，引导会创建新的 `assets.json`，不会扫描项目目录或读取文件内容。

```bash
rak evidence init --manifest assets.json --out graph.json --format json
```

单独保存返回记录中的 `graph_content_sha256`，作为经过审阅的基准摘要。将下面的 `SAVED_DIGEST` 和可选声明标识替换为自己的值：

```bash
rak evidence check graph.json --graph-sha256 SAVED_DIGEST --allow-unresolved-claim urn:rak:project:claim:main@1 --format markdown --out check.json
```

没有添加声明时，省略 `--allow-unresolved-claim` 参数。该参数只允许指定的、带有明确版本的声明保留“未裁定”状态；其他证据缺失或未解决的问题仍会阻止检查通过。

输出只允许写入新文件，本地重复检查时请使用新的报告文件名。

结果文件发生变化后，报告会呈现类似内容（以下为合成示例）：

| 问题文件 | 观察结果 | 待复核声明 |
| --- | --- | --- |
| results.csv | 文件内容与基准不一致（`IDENTITY_MISMATCH`） | main@1 |

声明的追溯路径：results.csv → 用户列出的证据 → main@1。

先复核文件变化和声明内容，再有意识地更新基准。文件内容匹配并不能证明声明成立，声明之间的关系由用户填写。

[实际运行生成的合成示例报告](examples/evidence_graph_demo/expected_guided_report.md) ·
[五分钟入门与 GitHub 任务摘要](docs/evidence_onboarding.md) ·
[使用独立保存的基准进行持续集成检查](docs/evidence_check.md) ·
[可重放的合成示例](examples/evidence_graph_demo/README.md)

## 公开发布前，审计并冻结机器学习仓库

现有的仓库审计功能继续保留，无需强制配置即可使用：

```bash
python -m pip install -e .
rak --version
rak audit .
rak audit examples/audit_demo/pass_repo
rak audit examples/audit_demo/warning_repo
set +e
rak audit examples/audit_demo/blocker_repo
RAK_BLOCKER_CODE=$?
set -e
test "$RAK_BLOCKER_CODE" -eq 2
```

`rak audit` 清点本地文件，执行机械检查，并读取可选的 `.rak/policy.yaml` 策略。检查通过不代表科学结论正确，也不是可复现性认证。详见[审计快速入门](docs/quickstart.md)。

## 研究代码发布流程

审计 → 冻结 → 校验 → 按策略判定。

```text
AUDIT → FREEZE → VERIFY → GATE
```

| 阶段 | 命令 | 用途 |
| --- | --- | --- |
| 审计 | `rak audit .` | 查找可直接观察的警告与发布阻断项，并应用可选的项目策略。 |
| 冻结 | `rak freeze ...` | 创建可移植、受策略约束的文件内容基准。 |
| 校验 | `rak verify ...` | 将当前纳入管理的文件内容与冻结基准比较。 |
| 策略判定 | `rak gate ...` | 按用户声明的策略评估用户声明的指标。 |

各阶段读取的证据、生成的记录及能力边界，见[工作流程指南](docs/research_release_workflow.md)。

## 重放完整审计示例

下面的命令依次检查当前源码工作目录、正常示例、警告示例，以及故意设置的发布阻断示例，不会把审计输出写进被检查的仓库。

```bash
python -m pip install -e .
rak --version
rak audit .
rak audit examples/audit_demo/pass_repo
rak audit examples/audit_demo/warning_repo
set +e
rak audit examples/audit_demo/blocker_repo
RAK_BLOCKER_CODE=$?
set -e
test "$RAK_BLOCKER_CODE" -eq 2
```

默认的 `--fail-on release-blocker` 策略下，警告的退出码为 0；使用 `--fail-on warning` 可让警告也阻止持续集成通过。`ABSTAIN`（弃权）、`UNRESOLVED`（未解决）和 `RELEASE_BLOCKER`（发布阻断）的退出码始终为 2。详见[审计命令约定](docs/audit_command.md)与[分步入门](docs/quickstart.md)。

## 项目策略

未提供配置时，`rak audit` 使用保守的内置策略 `rak-generic-release-v1`。仓库可以提供 `.rak/policy.yaml`，或通过 `--policy PATH` 指定策略，替换文件清单的分类规则并声明必需文件。通用的路径安全检查、自述文件与许可证存在性检查、符号链接报告和确定性清单检查仍会运行。

`policy.required_files` 中的每个值都必须是仓库内部、符合规范的相对文件路径，使用正斜杠。绝对路径、目录穿越、反斜杠、控制字符、不规范路径，以及通过符号链接逃离仓库的路径，都会作为策略错误拒绝处理；错误信息不会再次输出不安全的值。

可以查看[默认策略文件](configs/audit_policy.default.yaml)了解内置约定。策略文件仅作为数据处理，审计不会运行被检查项目的依赖。

## 机器可读输出

```bash
rak audit . --format json --output audit-result.json
```

规范化结果采用 [`researchauditkit.audit/v1`](schemas/audit-result-v1.schema.json) 格式。单项检查使用以下状态：

- `PASS`：通过。
- `WARNING`：警告。
- `RELEASE_BLOCKER`：发布阻断。
- `NOT_APPLICABLE`：不适用。
- `UNRESOLVED`：未解决。

总体结果使用 `PASS`、`WARNING`、`RELEASE_BLOCKER` 或 `ABSTAIN`。路径、文件内容和策略相同时，结果顺序与内容摘要具有确定性。

暂不提供 SARIF 输出。需要先定义并记录映射方式，才能在其结果与严重程度模型中保留“不适用”“未解决”状态，以及本工具不提供科学认证的边界。

## GitHub 自动化工作流组件

组合式组件会自行准备固定的 Python 运行环境，以及通过哈希锁定的 PyYAML 依赖。它只运行 `rak audit`，写入 GitHub 任务摘要，保留命令行退出码，无需访问令牌，也不会安装或执行被检查项目的代码。

环境准备依赖官方自动化组件和软件包基础设施；审计本身仍在本地进行，不上传仓库内容。确认第四个候选预发布版本存在后，使用对应的明确版本：

```yaml
- uses: ernestoleo777-dotcom/ResearchAuditKit@v0.1.0-rc.4
  with:
    path: .
    fail-on: release-blocker
```

本项目不发布可变的 `v0`、`v0.1`、`main` 或 `latest` 组件别名。如需更强的不可变性，可将标签替换为其解析后的完整提交哈希。详见 [GitHub 自动化集成指南](docs/github_action.md)。

## 进阶命令

主要使用流程不会移除或重命名现有命令：

```text
rak init --root REPO --policy POLICY
rak inventory --root REPO --policy POLICY --out DIR
rak freeze --root REPO --policy POLICY --baseline FILE [--force]
rak verify --root REPO --baseline FILE --out DIR
rak prediction-seal --input DECLARATION.json --out SEAL.json [--force]
rak prediction-verify --input DECLARATION.json --seal SEAL.json --out DIR
rak isolation-audit --root ROOT --manifest WORKSPACES.json --out DIR
rak evidence-index --roles ROLES.json --records RECORDS.json --out DIR
rak support-audit --data CSV --features a,b --discrete a,b --out DIR
rak pareto-audit --candidates CSV --objectives loss:min,cost:min --support-column COLUMN --out DIR
rak split-audit --data CSV --manifest CSV --id-column ID --out DIR
rak gate --metrics JSON --policy YAML --out DIR
rak deviation record --config YAML --out LEDGER.csv
rak claims evaluate --claims CSV --evidence CSV --out DIR
```

这些进阶命令需要各自文档中规定的输入，`rak audit` 不会猜测输入或自动调用它们。详见[命令参考](docs/command_reference.md)。

## 公开集成记录

[CoordCap](https://github.com/ernestoleo777-dotcom/CoordCap) 是目前首个、也是唯一经过核实的公开使用项目。它是维护者自己的项目，不能视为独立外部采用。

在该项目的[集成合并提交](https://github.com/ernestoleo777-dotcom/CoordCap/commit/14cef46b3813e20ee26266faebb72a72aad7ac76)中，第三个候选版本的[自动化组件](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/releases/tag/v0.1.0-rc.3)固定到[不可变的发布提交](https://github.com/ernestoleo777-dotcom/ResearchAuditKit/commit/72ee132038a36d8678da11e86d3b953726a5e9a7)，使用已提交的 `.rak/policy.yaml` 运行 `rak audit`，仅作为仓库完整性的机械预检查。

该项目[公开主分支上的成功运行记录](https://github.com/ernestoleo777-dotcom/CoordCap/actions/runs/33190211004)显示总体检查通过，并生成了 GitHub 任务摘要。详见[公开集成说明](docs/public_integrations.md)。

## 文档

以下链接保留现有文档；本页提供完整的简体中文自述说明，链接指向的进阶文档目前仍主要使用英文。

- [研究代码发布流程](docs/research_release_workflow.md)
- [审计命令](docs/audit_command.md)
- [快速入门](docs/quickstart.md)
- [GitHub 自动化集成](docs/github_action.md)
- [命令参考](docs/command_reference.md)
- [持续集成](docs/ci_integration.md)
- [扩展边界](docs/extension_boundaries.md)
- [能力限制](docs/limitations.md)
- [架构](docs/architecture.md)
- [公开集成](docs/public_integrations.md)
- [本项目候选发布包的证据预检查](docs/release_evidence_preflight.md)
- [项目状态](PROJECT_STATUS.md)
- [安全说明](SECURITY.md)
- [参与贡献](CONTRIBUTING.md)

ResearchAuditKit 是一个实验性的研究工程工具，按实际使用需求维护，采用 Apache 2.0 许可证。它尚无稳定版本，也未通过 PyPI 或 TestPyPI 分发。报告可能包含本地文件名与哈希，分享前请先检查生成的文件。

## 证据图

`rak evidence` 在现有审计命令之外，提供明确、带版本的证据图。可以使用以下命令：

- `rak evidence validate graph.json`：检查图结构。
- `rak evidence trace CLAIM_ID --graph graph.json`：追溯指定声明。
- `rak evidence doctor graph.json`：检查本地文件身份与图的健康状态。
- `rak evidence impact graph.json`：分析文件身份问题对已声明关系的影响。

新增格式为 `researchauditkit.evidence/v1`。输入中的关系与验证标签属于用户声明。文件哈希匹配只能作为当前文件内容的机械证据，不能据此作出科学裁定或推断历史文件身份。

可以从[资产清单初始化与可读报告](docs/evidence_onboarding.md)入手，或重放[合成命令行示例](examples/evidence_graph_demo/README.md)。通过[带基准摘要的项目检查](docs/evidence_check.md)，可在持续集成中检查明确列出的文件身份，同时保留声明的“未裁定”状态。

路径规则、资源限制、退出码与不确定性约定，见[证据图说明](docs/evidence_graph.md)。证据命令已包含在第四个候选版本中。
