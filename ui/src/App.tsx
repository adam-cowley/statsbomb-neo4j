import React, { useState } from 'react';

import { Pitch } from './components/pitch';
import {  useEvents } from './hooks';
import { reduceToPossession } from './utils';
import { Possession } from './types/Possession';
import { Timeline } from './components/timeline/timeline';

import './App.css';

function App() {
  // Keep an array of selected events in the App component state
  // This allows me to have a single <Pitch> component in the app
  // You'd probably not do this with react-router
  const [possession, setPossession] = useState<Possession | undefined>()
  // const { loading, events } = useEvents(69328)
  const { loading, events } = useEvents(3849389)

  if (loading) {
    return <div>Loading...</div>
  }

  const possessions = reduceToPossession(events)


  return (
    <div className="App">
      <Timeline current={possession} possessions={possessions} setPossession={setPossession} />

      {possession && <Pitch
        events={possession.events}
      />}
    </div>
  );
}

export default App;
