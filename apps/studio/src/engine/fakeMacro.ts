// SPDX-License-Identifier: GPL-3.0-only
import type { ModuleDescriptor, ModuleParam, ModulePort } from '../modules/types';

/** Studio simulation only, until the portable Macro module is promoted.
 * The real engine palette is exclusively its advertised catalogue. */
export const fakeMacroDescriptor = (): ModuleDescriptor & { data_slots: string[] } => ({
  id: 'essentials.macro', name: 'Macros', category: 'Control', data_slots: ['labels'],
  parameters: Array.from({ length: 8 }, (_, i): ModuleParam => ({
    id: 'knob' + (i + 1), name: 'Knob ' + (i + 1), minimum: 0, maximum: 1,
    default: 0, unit: '', taper: 'linear', step: 0, decimals: 3, modulatable: true,
  })),
  ports: Array.from({ length: 8 }, (_, i): ModulePort => ({
    id: 'out' + (i + 1), name: 'Out ' + (i + 1), direction: 'output',
    kind: 'signal', hint: 'cv_uni', poly: 'first', stereo_pair: null,
  })),
});
