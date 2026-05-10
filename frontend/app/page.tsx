import { LandingPageHero } from '@/components/pages/LandingPageHero';
import { LandingPageFeatures } from '@/components/pages/LandingPageFeatures';
import { LandingPageTechStack } from '@/components/pages/LandingPageTechStack';

export default function Home() {
  return (
    <div className="w-full">
      <LandingPageHero />
      <LandingPageFeatures />
      <LandingPageTechStack />
    </div>
  );
}
