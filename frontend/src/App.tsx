import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'

function App() {
  return (
    <>
      <div className="flex min-h-svh items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Budget Tracker</h1>
          <p className="text-muted-foreground">Frontend scaffold is working.</p>
          <Button>Get Started</Button>
        </div>
      </div>
      <Toaster />
    </>
  )
}

export default App
