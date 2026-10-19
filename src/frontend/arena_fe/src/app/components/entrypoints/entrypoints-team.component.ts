import { Component } from '@angular/core';

type TeamMember = {
  name: string;
  /** footnote marker shown after the name */
  mark?: '*' | '†';
  photo: string;
  affiliations: { lab: string; institution: string }[];
  email?: string;
  website?: string;
  linkedin?: string;
  x?: string;
};

const TEAM: TeamMember[] = [
  {
    name: 'Abdulrahman Alabdulkareem',
    mark: '*',
    photo: 'team/alabdulkareem.jpg',
    affiliations: [{ lab: 'InfoLab', institution: 'MIT CSAIL' }],
    email: 'arkareem@mit.edu',
    website: 'https://arkareem.com/',
    linkedin: 'https://www.linkedin.com/in/abdulrahman-alabdulkareem-493a8143/',
    x: 'https://x.com/AR_kareem_'
  },
  {
    name: 'David Mayo',
    photo: 'team/mayo.jpg',
    affiliations: [{ lab: 'InfoLab', institution: 'MIT CSAIL' }],
    email: 'dmayo2@mit.edu',
    website: 'http://david-mayo.com/',
    linkedin: 'https://www.linkedin.com/in/david-mayo-114a5b79/',
    x: 'https://x.com/dmayo_2'
  },
  {
    name: 'Kushagra Tiwary',
    photo: 'team/tiwary.jpg',
    affiliations: [
      { lab: 'InfoLab', institution: 'MIT CSAIL' },
      { lab: 'Camera Culture', institution: 'MIT Media Lab' }
    ],
    email: 'ktiwary@mit.edu',
    website: 'https://www.kushagratiwary.com/',
    linkedin: 'https://www.linkedin.com/in/ktiwary-mit/',
    x: 'https://x.com/ktiwarylab'
  },
  {
    name: 'Boris Katz',
    photo: 'team/katz.jpg',
    affiliations: [{ lab: 'InfoLab', institution: 'MIT CSAIL' }],
    email: 'boris@mit.edu',
    website: 'https://people.csail.mit.edu/boris/boris.html'
  },
  {
    name: 'Brian Cheung',
    mark: '†',
    photo: 'team/cheung.jpg',
    affiliations: [{ lab: 'Disco Lab', institution: 'UCSF' }],
    email: 'bcheung@ucsf.edu',
    website: 'https://discolab.org/',
    linkedin: 'https://www.linkedin.com/in/brianwcheung/',
    x: 'https://x.com/thisismyhat'
  }
];

@Component({
  selector: 'arena-entrypoint-team',
  standalone: true,
  templateUrl: './entrypoints-team.component.html',
  styleUrl: './entrypoints-team.component.scss'
})
export class ArenaEntrypointTeamComponent {
  readonly team = TEAM;
}
