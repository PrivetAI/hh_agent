// utils/areas.ts
import { Area } from '../types'

export class AreasHelper {
  static flattenRussianAreas(areas: Area[]): Area[] {
    const russia = areas.find((country: Area) => country.id === '113')
    if (!russia || !russia.areas) return []

    const flatAreas: Area[] = []
    
    russia.areas.forEach((region: Area) => {
      flatAreas.push(region)
      if (region.areas) {
        region.areas.forEach((city: Area) => {
          flatAreas.push(city)
        })
      }
    })
    
    return flatAreas
  }

  static formatAreaName(area: Area): string {
    return area.parent_id ? `— ${area.name}` : area.name
  }
}