import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import EventExplorer from '@/pages/EventExplorer'
import AccessPoints from '@/pages/AccessPoints'
import Alerts from '@/pages/Alerts'
import AssetInventory from '@/pages/AssetInventory'
import DetectionRules from '@/pages/DetectionRules'
import DataSources from '@/pages/DataSources'
import SettingsPage from '@/pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="events" element={<EventExplorer />} />
          <Route path="access-points" element={<AccessPoints />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="assets" element={<AssetInventory />} />
          <Route path="rules" element={<DetectionRules />} />
          <Route path="sources" element={<DataSources />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
