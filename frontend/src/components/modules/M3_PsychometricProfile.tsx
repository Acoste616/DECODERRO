/**
 * ULTRA v3.0 - Module 3: Psychometric Profile
 * ============================================
 * 
 * Renders dominant DISC profile and Big Five traits radar chart
 */

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { useTranslation } from '../../utils/i18n';
import type { IM3PsychometricProfile } from '../../types';

interface Props {
  data: IM3PsychometricProfile;
}

export default function M3_PsychometricProfile({ data }: Props) {
  const { t } = useTranslation();

  // Prepare chart data for Big Five
  const chartData = [
    { trait: t('modules.m3_openness'), value: data.big_five_traits.openness.score },
    { trait: t('modules.m3_conscientiousness'), value: data.big_five_traits.conscientiousness.score },
    { trait: t('modules.m3_extraversion'), value: data.big_five_traits.extraversion.score },
    { trait: t('modules.m3_agreeableness'), value: data.big_five_traits.agreeableness.score },
    { trait: t('modules.m3_neuroticism'), value: data.big_five_traits.neuroticism.score },
  ];

  // DISC colors
  const discColors: { [key: string]: string } = {
    D: 'bg-red-500',
    I: 'bg-yellow-500',
    S: 'bg-green-500',
    C: 'bg-blue-500',
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        🧠 {t('modules.m3_title')}
      </h3>

      {/* Dominant DISC */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          {t('modules.m3_dominant_disc')}
        </h4>
        <div className="flex items-center gap-3">
          <div className={`w-16 h-16 rounded-full ${discColors[data.dominant_disc.type] || 'bg-gray-500'} flex items-center justify-center`}>
            <span className="text-2xl font-bold text-white">{data.dominant_disc.type}</span>
          </div>
          <div className="flex-1">
            <div className="font-semibold">{t(`modules.m3_disc_${data.dominant_disc.type.toLowerCase()}`)}</div>
            <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              {data.dominant_disc.rationale}
            </div>
          </div>
        </div>
      </div>

      {/* Big Five Radar Chart */}
      <div>
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          {t('modules.m3_big_five')}
        </h4>
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart data={chartData}>
            <PolarGrid stroke="#666" />
            <PolarAngleAxis dataKey="trait" tick={{ fill: '#999', fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#999', fontSize: 10 }} />
            <Radar
              name="Big Five"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.5}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
