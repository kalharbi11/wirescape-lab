// SPDX-License-Identifier: GPL-3.0-only
import { buildPlayerBundle, safeScriptName, type ExportPatch, type PlayerBundle } from './bundleExport';
import { el, testid } from './dom';
import { Modal } from './Modal';
import type { PatchV2 } from '../patch/types';

interface DirectoryHandle extends FileSystemDirectoryHandle {
  keys(): AsyncIterableIterator<string>;
  getDirectoryHandle(name: string, options?: FileSystemGetDirectoryOptions): Promise<DirectoryHandle>;
}
type DirectoryPicker = (options: { mode: 'readwrite' }) => Promise<DirectoryHandle>;
const MAX_FILE = 2 * 1024 * 1024;
const MAX_FILES = 256;
const MAX_BUNDLE = 64 * 1024 * 1024;
interface NativeBundleWriter {
  write(input: { playerJson: string; patches: PlayerBundle['patches']; scripts: { name: string; bytes: Uint8Array }[] }): Promise<{ name: string } | null>;
}

async function writeFile(dir: DirectoryHandle, name: string, content: string | Blob): Promise<void> {
  const handle = await dir.getFileHandle(name, { create: true });
  const stream = await handle.createWritable();
  try {
    await stream.write(content);
    await stream.close();
  } catch (error) {
    await stream.abort().catch(() => {});
    throw error;
  }
}

/** Require a new/empty folder. Never overwrite an existing Player bundle. Write
 * the manifest last, so an interrupted export has no committed setlist. */
export async function writePlayerBundle(dir: DirectoryHandle, bundle: PlayerBundle, scripts: ReadonlyMap<string, File>): Promise<void> {
  if (!(await dir.keys().next()).done) throw new Error('Choose an empty folder; existing files are not overwritten.');
  for (const name of bundle.scripts) {
    const file = scripts.get(name);
    if (!file || !safeScriptName(name) || file.size > MAX_FILE) throw new Error(`Missing or oversized script: ${name}`);
  }
  const patchesDir = await dir.getDirectoryHandle('patches', { create: true });
  const scriptsDir = await dir.getDirectoryHandle('scripts', { create: true });
  for (const patch of bundle.patches) await writeFile(patchesDir, patch.name, patch.text);
  for (const name of bundle.scripts) await writeFile(scriptsDir, name, scripts.get(name)!);
  await writeFile(dir, 'player.json', JSON.stringify(bundle.player, null, 2) + '\n');
}

function labeledInput(label: string, input: HTMLInputElement): HTMLElement {
  const row = el('label', 'field');
  row.append(el('span', 'field-label', label), input);
  return row;
}

/** Snapshot the current authored document. Additional files are read without
 * loading them into Studio or changing the native Save target. */
export function showBundleExport(modal: Modal, current: ExportPatch): void {
  const title = testid(el('input', 'input-text'), 'bundle-title');
  title.value = current.title;
  const patches = testid(el('input'), 'bundle-patches');
  patches.type = 'file'; patches.multiple = true; patches.accept = '.json,application/json';
  const scripts = testid(el('input'), 'bundle-scripts');
  scripts.type = 'file'; scripts.multiple = true; scripts.accept = '.py';
  const status = testid(el('p', 'muted'), 'bundle-status');
  status.setAttribute('role', 'status');
  const summary = el('p', 'muted');
  const write = testid(el('button', 'btn', 'Choose empty folder and export'), 'bundle-write');
  write.type = 'button';
  let selection = 0, ready: { bundle: PlayerBundle; files: Map<string, File> } | null = null, busy = false;
  const update = async () => {
    const epoch = ++selection;
    ready = null; write.disabled = true;
    status.textContent = ''; summary.textContent = '';
    try {
      const extra = [...(patches.files ?? [])];
      const scriptFiles = [...(scripts.files ?? [])];
      if (extra.length + 1 > MAX_FILES || scriptFiles.length > MAX_FILES)
        throw new Error('Too many files selected.');
      const inputs = [current];
      for (const file of extra) {
        if (file.size > MAX_FILE) throw new Error(`Patch exceeds 2 MiB: ${file.name}`);
        const patch = JSON.parse(await file.text()) as PatchV2;
        inputs.push({ title: file.name.replace(/\.json$/i, ''), patch });
      }
      const bundle = buildPlayerBundle(title.value, inputs);
      const encoder = new TextEncoder();
      const sizes = bundle.patches.map(p => encoder.encode(p.text).length);
      const manifestSize = encoder.encode(JSON.stringify(bundle.player, null, 2) + '\n').length;
      if (sizes.some(size => size > MAX_FILE) || manifestSize > MAX_FILE)
        throw new Error('An exported patch or manifest exceeds 2 MiB.');
      const files = new Map<string, File>();
      for (const file of scriptFiles) {
        if (!safeScriptName(file.name) || file.size > MAX_FILE || files.has(file.name))
          throw new Error(`Invalid, duplicate or oversized script: ${file.name}`);
        files.set(file.name, file);
      }
      if (epoch !== selection) return;
      summary.textContent = 'Setlist: ' + bundle.player.setlist.map(e => e.title).join(' → ');
      const missing = bundle.scripts.filter(name => !files.has(name));
      if (missing.length) throw new Error('Select linked scripts: ' + missing.join(', '));
      const total = sizes.reduce((a, b) => a + b, manifestSize) + bundle.scripts.reduce((n, name) => n + files.get(name)!.size, 0);
      if (total > MAX_BUNDLE) throw new Error('Bundle exceeds 64 MiB.');
      ready = { bundle, files };
      write.disabled = busy;
    } catch (e) {
      if (epoch === selection) status.textContent = e instanceof Error ? e.message : 'Invalid bundle.';
    }
  };
  title.addEventListener('input', () => void update());
  patches.addEventListener('change', () => void update());
  scripts.addEventListener('change', () => void update());
  write.addEventListener('click', async () => {
    if (!ready || busy) return;
    const picked = ready;
    const host = window as unknown as { showDirectoryPicker?: DirectoryPicker; wirescapeBundleExport?: NativeBundleWriter };
    const picker = host.showDirectoryPicker, native = host.wirescapeBundleExport;
    if (!picker && !native) {
      status.textContent = 'Folder export is unavailable in this browser. Open Studio in a browser with directory access.';
      return;
    }
    busy = true; write.disabled = true;
    title.disabled = patches.disabled = scripts.disabled = true;
    try {
      if (native) {
        const scriptBytes = await Promise.all(picked.bundle.scripts.map(async name => ({
          name, bytes: new Uint8Array(await picked.files.get(name)!.arrayBuffer()),
        })));
        const saved = await native.write({ playerJson: JSON.stringify(picked.bundle.player, null, 2) + '\n',
          patches: picked.bundle.patches, scripts: scriptBytes });
        if (!saved) { status.textContent = 'Export cancelled.'; return; }
      } else {
        // Call from the click itself, before any asynchronous file operations.
        const dir = await picker!.call(window, { mode: 'readwrite' });
        await writePlayerBundle(dir, picked.bundle, picked.files);
      }
      status.textContent = `Exported ${picked.bundle.patches.length} patches and ${picked.bundle.scripts.length} scripts.`;
    } catch (error) {
      status.textContent = error instanceof DOMException && error.name === 'AbortError' ? 'Export cancelled.'
        : error instanceof Error ? error.message : 'Could not export bundle.';
    } finally {
      busy = false; write.disabled = !ready;
      title.disabled = patches.disabled = scripts.disabled = false;
    }
  });
  modal.body.replaceChildren(
    el('p', '', 'Export the current patch first, then any selected additional patch files in the displayed order. Select linked Python files explicitly; export never runs them.'),
    labeledInput('Bundle title', title), labeledInput('Additional patches', patches),
    labeledInput('Linked scripts', scripts), summary, write, status);
  modal.open('Export Player bundle');
  void update();
}
