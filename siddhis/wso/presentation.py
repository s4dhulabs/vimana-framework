# -*- coding: utf-8 -*-
# Human-friendly terminal presenter for WSO aggregate reports.

from __future__ import annotations

from typing import Any, Dict, List

from neotermcolor import colored


SEVERITY_COLORS = {
    'high': 'red',
    'medium': 'yellow',
    'low': 'blue',
    'info': 'white',
}

SEVERITY_ORDER = ('high', 'medium', 'low', 'info')


def is_interactive(handler: dict) -> bool:
    """True when human terminal output should be shown."""
    if handler.get('ci_mode') or handler.get('json_output') or handler.get('no_metadata'):
        return False
    if handler.get('quiet_output'):
        return False
    return True


def print_run_header(base_url: str, steps: List[str], spec_id: str = None) -> None:
    print(colored('\n[*] WSO — WebSockets Orchestrator', 'cyan'))
    print(f"    Target : {base_url or 'n/a'}")
    if spec_id:
        print(f"    Spec   : {colored(str(spec_id), 'cyan')}")
    chain = ' → '.join(steps) if steps else '(none)'
    print(f"    Chain  : {chain}")
    print()


def print_scan_start(base_url: str) -> None:
    print(colored(f'[*] Scanning OpenAPI on {base_url}…', 'cyan'))


def print_scan_done(spec_id: str) -> None:
    print(colored(f'[+] Spec registered: {spec_id}', 'green'))
    print()


def print_step_start(name: str, index: int, total: int) -> None:
    print(colored(f'[*] Step {index}/{total}: {name}', 'cyan'))


def print_step_done(name: str, step_summary: dict = None, error: str = None) -> None:
    if error:
        print(colored(f'[!] {name} failed: {error}', 'red'))
        return
    summary = step_summary or {}
    high = summary.get('findings_high', 0)
    medium = summary.get('findings_medium', 0)
    total = summary.get('findings_total', 0)
    if high:
        status = colored('FAIL', 'red')
    elif medium:
        status = colored('ISSUES', 'yellow')
    else:
        status = colored('PASS', 'green')
    print(
        f"    {status}  findings={total} "
        f"(high={colored(str(high), 'red' if high else 'white')}, "
        f"medium={colored(str(medium), 'yellow' if medium else 'white')})"
    )
    print()


def print_report(report: Dict[str, Any]) -> None:
    """Render aggregate WSO report for interactive terminal use."""
    summary = report.get('summary') or {}
    steps = report.get('steps') or []
    findings = report.get('findings') or []

    print(colored('─' * 64, 8))
    print(colored(' WSO Results', 'green', attrs=['bold']))
    print(colored('─' * 64, 8))
    print(f"  Target     : {report.get('base_url') or 'n/a'}")
    print(f"  Spec ID    : {report.get('spec_id') or 'n/a'}")
    print(f"  Steps      : {summary.get('steps', len(steps))}")
    print(
        f"  Findings   : {summary.get('findings_total', 0)} "
        f"(high={summary.get('findings_high', 0)}, "
        f"medium={summary.get('findings_medium', 0)}, "
        f"low={summary.get('findings_low', 0)}, "
        f"info={summary.get('findings_info', 0)})"
    )
    passed = summary.get('passed', False)
    gate = colored('PASSED', 'green') if passed else colored('FAILED', 'red')
    print(f"  CI gate    : {gate}")
    print()

    if steps:
        print(colored('  Steps', 'cyan'))
        for step in steps:
            name = step.get('name') or step.get('plugin') or '?'
            err = step.get('error')
            s = step.get('summary') or {}
            if err:
                line = f"    • {name}: {colored('ERROR', 'red')} — {err}"
            else:
                high = s.get('findings_high', 0)
                medium = s.get('findings_medium', 0)
                if high:
                    mark = colored('fail', 'red')
                elif medium:
                    mark = colored('issues', 'yellow')
                else:
                    mark = colored('ok', 'green')
                line = (
                    f"    • {name}: {mark}  "
                    f"high={s.get('findings_high', 0)} medium={s.get('findings_medium', 0)}"
                )
            print(line)
        print()

    actionable = [
        f for f in findings
        if f.get('severity') in ('high', 'medium')
    ]
    # Sort by severity then plugin
    def _sort_key(item: dict):
        sev = item.get('severity', 'info')
        try:
            sev_idx = SEVERITY_ORDER.index(sev)
        except ValueError:
            sev_idx = 99
        return (sev_idx, item.get('plugin') or '', item.get('check') or '')

    ordered = sorted(findings, key=_sort_key)

    if not ordered:
        print(colored('  [*] No findings from the WebSocket chain.', 'yellow'))
        print()
        return

    print(colored('  Findings', 'cyan'))
    for item in ordered:
        sev = item.get('severity', 'info')
        color = SEVERITY_COLORS.get(sev, 'white')
        plugin = item.get('plugin') or 'wso'
        target = item.get('target') or ''
        check = item.get('check') or ''
        detail = item.get('detail') or ''
        print(
            f"    [{colored(sev.upper(), color)}] "
            f"[{colored(plugin, 45)}] "
            f"{target} — {check}: {detail}"
        )
    print()

    if actionable and not passed:
        print(colored(
            f'  [!] {len(actionable)} actionable finding(s) '
            f'({summary.get("findings_high", 0)} high).',
            'red',
        ))
        print()
